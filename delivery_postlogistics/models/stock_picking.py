# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from operator import attrgetter

from odoo import _, exceptions, fields, models

from ..postlogistics.web_service import PostlogisticsWebService


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_fixed_date = fields.Date(
        "Fixed delivery date", help="Specific delivery date (ZAW3217)"
    )

    # TODO: consider refactoring these fields using a partner relation instead
    delivery_place = fields.Char(
        "Delivery Place", help="For Deposit item service (ZAW3219)"
    )
    delivery_phone = fields.Char(
        "Phone", help="For notify delivery by telephone (ZAW3213)"
    )
    delivery_mobile = fields.Char(
        "Mobile", help="For notify delivery by telephone (ZAW3213)"
    )

    def _get_packages_from_picking(self):
        """ Get all the packages from the picking """
        self.ensure_one()
        operation_obj = self.env["stock.move.line"]
        operations = operation_obj.search(
            [
                "|",
                ("package_id", "!=", False),
                ("result_package_id", "!=", False),
                ("picking_id", "=", self.id),
            ]
        )
        package_ids = []
        for operation in operations:
            # Take the destination package. If empty, the package is
            # moved so take the source one.
            package_ids.append(
                operation.result_package_id.id or operation.package_id.id
            )

        packages = self.env["stock.quant.package"].browse(package_ids)
        return packages

    def get_shipping_label_values(self, label):
        self.ensure_one()
        return {
            "name": label["name"],
            "res_id": self.id,
            "res_model": "stock.picking",
            "datas": label["file"],
            "file_type": label["file_type"],
        }

    def attach_shipping_label(self, label):
        """Attach a label returned by generate_shipping_labels to a picking"""
        self.ensure_one()
        data = self.get_shipping_label_values(label)
        context_attachment = self.env.context.copy()
        # remove default_type setted for stock_picking
        # as it would try to define default value of attachement
        if "default_type" in context_attachment:
            del context_attachment["default_type"]
        return (
            self.env["postlogistics.shipping.label"]
            .with_context(context_attachment)
            .create(data)
        )

    def _set_a_default_package(self):
        """ Pickings using this module must have a package
            If not this method put it one silently
        """
        for picking in self:
            move_lines = picking.move_line_ids.filtered(
                lambda s: not (s.package_id or s.result_package_id)
            )
            if move_lines:
                default_packaging = (
                    picking.carrier_id.postlogistics_default_packaging_id
                )
                package = self.env["stock.quant.package"].create(
                    {
                        "packaging_id": default_packaging
                        and default_packaging.id
                        or False
                    }
                )
                move_lines.write({"result_package_id": package.id})

    def postlogistics_cod_amount(self):
        """ Return the Postlogistic Cash on Delivery amount of a picking

        If the picking delivers the whole sales order, we use the total
        amount of the sales order.

        Otherwise, we don't know the value of each picking so we raise
        an error.  The user has to create packages with the cash on
        delivery price on each package.
        """
        self.ensure_one()
        order = self.sale_id
        if not order:
            return 0.0
        if len(order) > 1:
            raise exceptions.Warning(
                _(
                    "The cash on delivery amount must be manually specified "
                    "on the packages when a package contains products "
                    "from different sales orders."
                )
            )
        order_moves = order.mapped("order_line.procurement_ids.move_ids")
        picking_moves = self.move_lines
        # check if the package delivers the whole sales order
        if order_moves != picking_moves:
            raise exceptions.Warning(
                _(
                    "The cash on delivery amount must be manually specified "
                    "on the packages when a sales order is delivered "
                    "in several delivery orders."
                )
            )
        return order.amount_total

    def info_from_label(self, label, zpl_patch_string=False):
        tracking_number = label["tracking_number"]
        data = base64.b64decode(label["binary"])

        # Apply patch for zpl file
        if label["file_type"] == "zpl2" and zpl_patch_string:
            data = base64.b64encode(
                base64.b64decode(data)
                .decode("cp437")
                .replace("^XA", zpl_patch_string)
                .encode("utf-8")
            )
        return {
            "file": data,
            "file_type": label["file_type"],
            "name": tracking_number + "." + label["file_type"],
        }

    def write_tracking_number_label(self, label_result, packages):
        """
        If there are no pack defined, write tracking_number on picking
        otherwise, write it on parcel_tracking field of each pack.
        Note we can receive multiple labels for a same package
        """
        zpl_patch_string = self.carrier_id.zpl_patch_string

        labels = []
        if not packages:
            label = label_result[0]["value"][0]
            self.carrier_tracking_ref = label["tracking_number"]
            labels.append(self.info_from_label(label, zpl_patch_string))

        tracking_refs = []
        for package in packages:
            tracking_numbers = []
            for label in label_result:
                for label_value in label["value"]:
                    if package.name in label_value["item_id"].split("+")[-1]:
                        tracking_numbers.append(label_value["tracking_number"])
                        labels.append(
                            self.info_from_label(label_value, zpl_patch_string)
                        )
            package.parcel_tracking = "; ".join(tracking_numbers)
            tracking_refs += tracking_numbers

        existing_tracking_ref = (
            self.carrier_tracking_ref and self.carrier_tracking_ref.split("; ") or []
        )
        self.carrier_tracking_ref = "; ".join(existing_tracking_ref + tracking_refs)
        return labels

    def _generate_postlogistics_label(
        self, webservice_class=None, package_ids=None, skip_attach_file=False
    ):
        """ Generate labels and write tracking numbers received """
        self.ensure_one()
        user = self.env.user
        company = user.company_id
        if webservice_class is None:
            webservice_class = PostlogisticsWebService

        if package_ids is None:
            packages = self._get_packages_from_picking()
            packages = packages.sorted(key=attrgetter("name"))
        else:
            # restrict on the provided packages
            package_obj = self.env["stock.quant.package"]
            packages = package_obj.browse(package_ids)

        web_service = webservice_class(company)

        # Do not generate label for packages that are already done
        packages = packages.filtered(lambda p: not p.parcel_tracking)

        label_results = web_service.generate_label(self, packages)

        # Process the success packages first
        success_label_results = [
            label for label in label_results if "errors" not in label
        ]
        failed_label_results = [label for label in label_results if "errors" in label]

        # Case when there is a failed label, rollback odoo data
        if failed_label_results:
            self._cr.rollback()

        labels = self.write_tracking_number_label(success_label_results, packages)

        if not skip_attach_file:
            for label in labels:
                self.attach_shipping_label(label)

        if failed_label_results:
            # Commit the change to save the changes,
            # This ensures the label pushed recored correctly in Odoo
            self._cr.commit()
            error_message = "\n".join(label["errors"] for label in failed_label_results)
            raise exceptions.Warning(error_message)
        return labels

    def generate_postlogistics_shipping_labels(self, package_ids=None):
        """ Add label generation for Postlogistics """
        self.ensure_one()
        return self._generate_postlogistics_label(package_ids=package_ids)
