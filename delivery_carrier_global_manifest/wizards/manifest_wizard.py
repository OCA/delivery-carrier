# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import _, api, exceptions, fields, models


class ManifestWizard(models.TransientModel):
    _inherit = "manifest.wizard"

    carrier_id = fields.Many2one(
        required=False,
    )
    global_carrier_ids = fields.Many2many(
        string="Global Carriers",
        comodel_name="delivery.carrier",
        domain=[("include_in_global_manifest", "=", True)],
        compute="_compute_global_carrier_ids",
        store=True,
        readonly=False,
    )
    global_manifest_query = fields.Boolean(
        string="Global Manifest",
        help="A global manifest query generates a generic global manifest "
        "report using all carriers configured to be included on it",
    )
    company_id = fields.Many2one(
        comodel_name="res.company", default=lambda self: self.env.company
    )

    @api.depends("company_id")
    def _compute_global_carrier_ids(self):
        for rec in self:
            rec.global_carrier_ids = (
                self.env["delivery.carrier"]
                .search(
                    [
                        ("include_in_global_manifest", "=", True),
                        ("company_id", "in", [False, rec.company_id.id]),
                    ]
                )
                .ids
            )

    def _get_global_manifest_pickings(self):
        self.ensure_one()
        search_args = [
            ("carrier_id", "in", self.global_carrier_ids.ids),
            ("date_done", ">=", self.from_date),
            ("state", "=", "done"),
            ("picking_type_code", "=", "outgoing"),
        ]
        if self.to_date:
            search_args.append(("date_done", "<=", self.to_date))
        return self.env["stock.picking"].search(
            search_args, order="carrier_id, partner_id"
        )

    def get_manifest_file(self):
        self.ensure_one()
        if not self.global_manifest_query:
            return super().get_manifest_file()

        pickings = self._get_global_manifest_pickings()
        if not pickings:
            raise exceptions.ValidationError(_("There are no pickings to proceed"))
        report_pdf = self.env["ir.actions.report"]._render(
            "delivery_carrier_global_manifest.action_global_carrier_manifest",
            [self.id],
            {"pickings": pickings},
        )[0]
        self.write(
            {
                "state": "file",
                "file_out": base64.b64encode(report_pdf),
                "filename": _("global-manifest.pdf"),
            }
        )
        return {
            "name": _("Manifest"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "manifest.wizard",
            "view_id": self.env.ref(
                "base_delivery_carrier_label.manifest_wizard_form"
            ).id,
            "res_id": self.id,
            "target": "new",
        }
