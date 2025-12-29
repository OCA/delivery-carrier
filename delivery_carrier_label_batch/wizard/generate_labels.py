# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import codecs
import logging
from itertools import groupby

from psycopg2 import OperationalError

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval

from odoo.addons.queue_job.delay import chain
from odoo.addons.queue_job.delay import group as job_group
from odoo.addons.queue_job.exception import RetryableJobError

from ..pdf_utils import assemble_pdf
from ..zpl_utils import assemble_zpl2, assemble_zpl2_single_images

_logger = logging.getLogger(__name__)


class DeliveryCarrierLabelGenerate(models.TransientModel):
    _name = "delivery.carrier.label.generate"
    _description = "Generate labels from batch pickings"

    def _get_batch_ids(self):
        res = False
        active_model = self.env.context.get("active_model")
        if active_model == "stock.picking.batch":
            if active_ids := self.env.context.get("active_ids"):
                res = active_ids
        return res

    batch_ids = fields.Many2many(
        "stock.picking.batch", string="Picking Batch", default=_get_batch_ids
    )
    generate_new_labels = fields.Boolean(
        "Generate new labels",
        default=False,
        help="If this option is used, new labels will be "
        "generated for the packs even if they already have one.\n"
        "The default is to use the existing label.",
    )

    @api.model
    def _get_packs(self, batch):
        operations = batch.move_line_ids  # pack_operation_ids
        operations = sorted(
            operations, key=lambda r: r.result_package_id.name or r.package_id.name
        )
        for pack, grp_operations in groupby(
            operations, key=lambda r: r.result_package_id or r.package_id
        ):
            pack_label = self._find_pack_label(pack)
            # TODO we should maybe try: pack_labelS = _find_pack_labelS(pack)
            # then iterate on paclk_labels
            yield (
                pack,
                self.env["stock.move.line"].browse([o.id for o in grp_operations]),
                pack_label,
            )

    @api.model
    def _find_pack_label(self, pack):
        label_obj = self.env["shipping.label"]
        domain = [("package_id", "=", pack.id)]
        return label_obj.search(domain, order="create_date DESC", limit=1)

    def _do_generate_labels(self, group):
        """Generate a label in a thread safe context
        Here we declare a specific cursor so do not launch
        too many threads
        """
        self.ensure_one()
        jobs = []
        for pack, picking, _label in group:
            _logger.debug("Generating label for pack %s", pack.name)
            job = self.delayable().retriable_send_to_shipper(picking)
            jobs.append(job)
        return jobs

    def retriable_send_to_shipper(self, picking):
        """Wrapper to call send_to_shipper in a retriable way"""
        self.ensure_one()
        try:
            picking.send_to_shipper()
        except OperationalError as oe:
            _logger.error("Error sending to shipper: %s", oe.diag)
            raise RetryableJobError(
                oe.diag,
                seconds=3,
                # ignore_retry=True,
            ) from oe

    def _generate_all_labels(self, batch):
        self.ensure_one()

        # If we have more than one pack in a picking, we must ensure
        # they are not executed concurrently or we will have concurrent
        # transaction errors. So we process them in the same thread.
        # We put them in the same 'group' and this group will be passed
        # as a whole to a thread worker.
        groups = {}
        for pack, operations, label in self._get_packs(batch):
            if not label or self.generate_new_labels:
                picking = operations[0].picking_id
                groups.setdefault(picking.id, []).append((pack, picking, label))

        jobs = []
        for group in groups.values():
            jobs.extend(self._do_generate_labels(group))
        return jobs

    def generate_pdf_summary(self, batch):
        self.ensure_one()

        zpl2_batch_merge = safe_eval(
            self.env["ir.config_parameter"].get_param("zpl2.batch.merge")
        )

        labels = []
        str_out = f"Labels generated for batch {batch.name}: \n"
        labels_out = []
        for pack in batch.move_line_ids.result_package_id:
            label = self._find_pack_label(pack)
            if not label:
                continue
            label_name = pack.parcel_tracking or pack.name
            labels.append((label.file_type, label.attachment_id.datas, label_name))
            labels_out.append(label_name)

        labels_by_f_type = self._group_labels_by_file_type(labels)
        for f_type, labels in labels_by_f_type.items():
            if f_type == "zpl2" and not zpl2_batch_merge:
                # We do not want to merge zpl2
                # because too big file can failed on zebra printers
                for label in labels:
                    f_name = label["name"]
                    filename = f"{f_name}.{f_type}"
                    data = {
                        "name": filename,
                        "res_id": batch.id,
                        "res_model": "stock.picking.batch",
                        "datas": label["data"],
                    }
                    self.env["ir.attachment"].create(data)
            else:
                labels_bin = [
                    codecs.decode(label["data"], "base64") for label in labels if label
                ]
                filename = batch.name + "." + f_type

                filedata = self._concat_files(f_type, labels_bin)
                if not filedata:
                    # Merging of `f_type` not supported, so we cannot
                    # create the attachment
                    continue
                data = {
                    "name": filename,
                    "res_id": batch.id,
                    "res_model": "stock.picking.batch",
                    "datas": codecs.encode(filedata, "base64"),
                }
            self.env["ir.attachment"].create(data)

            return str_out + "\n".join(sorted(labels_out))

    def _check_pickings(self):
        """Check pickings have at least one pack"""
        missing_packages = self.env["stock.picking"]
        for batch in self.batch_ids:
            for picking in batch.picking_ids:
                if not picking.has_packages:
                    missing_packages |= picking
        if missing_packages:
            package_list = "\n".join(missing_packages.mapped("name"))
            msg = self.env._(
                "Impossible to generate the labels."
                f" Those pickings don't have packages:\n{package_list}"
            )
            raise exceptions.UserError(msg)

    def action_generate_labels(self):
        """
        Call the creation of the delivery carrier label
        of the missing labels and get the existing ones
        Then merge all of them in a single PDF

        """
        self.ensure_one()

        # TODO ensure there is no pending jobs for those batches

        if not self.batch_ids:
            raise exceptions.UserError(self.env._("No picking batch selected"))

        # It shouldn't be possible to print labels when packages are missing
        operations = self.batch_ids.move_line_ids
        packages = operations.result_package_id or operations.package_id
        if not packages:
            raise exceptions.UserError(self.env._("Packages are missing"))

        self._check_pickings()

        to_generate = self.batch_ids

        job_groups = []

        if self.generate_new_labels:
            job_purge = to_generate.delayable().purge_tracking_references()
            job_groups.append(job_group(job_purge))
        else:
            already_generated_ids = (
                self.env["ir.attachment"]
                .search(
                    [
                        ("res_model", "=", "stock.picking.batch"),
                        ("res_id", "in", self.batch_ids.ids),
                    ]
                )
                .mapped("res_id")
            )
            to_generate = to_generate.filtered(
                lambda rec: rec.id not in already_generated_ids
            )

        if not to_generate:
            raise exceptions.UserError(
                self.env._("No labels to generate for the selected batches.")
            )

        batch_generate = self.env["queue.job.batch"].get_new_batch(
            "Generate labels for pickings"
        )
        batch_summary = self.env["queue.job.batch"].get_new_batch(
            "Generate summary PDFs"
        )

        job_summaries = []

        for batch in to_generate:
            jobs = self.with_context(job_batch=batch_generate)._generate_all_labels(
                batch
            )
            job_groups.append(job_group(*jobs))

            job_summary = (
                self.with_context(job_batch=batch_summary)
                .delayable()
                .generate_pdf_summary(batch)
            )
            job_groups.append(job_group(job_summary))
            job_summaries.append(job_summary)

        chainnable = chain(*job_groups)
        chainnable.delay()

        job_count = (
            len(batch_summary.job_ids.ids)
            + len(batch_generate.job_ids.ids)
            + self.generate_new_labels
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Label generation"),
                "message": _(
                    """%s job(s) have been created for label generation.
                    Labels will be available as soon as those jobs are finished."""
                )
                % (job_count),
                "type": "warning",
                "next": {
                    "type": "ir.actions.client",
                    "tag": "soft_reload",
                },
            },
        }

    @api.model
    def _group_labels_by_file_type(self, labels):
        res = {}
        _logger.debug("Grouping %d labels by file type", len(labels))
        _logger.debug("Labels: %s", labels)
        for f_type, label, label_name in labels:
            res.setdefault(f_type, [])
            res[f_type].append({"data": label, "name": label_name})
        return res

    @api.model
    def _concat_files(self, file_type, files):
        if file_type == "pdf":
            return assemble_pdf(files)
        if file_type == "zpl2":
            zpl2_single_images = safe_eval(
                self.env["ir.config_parameter"].get_param(
                    "zpl2.assembler.single.images"
                )
            )
            if zpl2_single_images:
                return assemble_zpl2_single_images(files)
            else:
                return assemble_zpl2(files)
        # Merging files of `file_type` not supported, we return nothing
        return
