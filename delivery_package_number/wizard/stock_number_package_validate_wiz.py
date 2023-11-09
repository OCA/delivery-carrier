# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockNumberPackageValidateWiz(models.TransientModel):
    _inherit = "stock.number.package.mixin"
    _name = "stock.number.package.validate.wizard"
    _description = "Wizard to force set number of pickings when validate"

    pick_ids = fields.Many2many("stock.picking", "stock_picking_number_package_rel")

    def process(self):
        if self.number_of_packages:
            self.pick_ids.write({"number_of_packages": self.number_of_packages})
        # put context key for avoiding `base_delivery_carrier_label` auto-packaging feature
        res = self.pick_ids.with_context(
            set_default_package=False, bypass_set_number_of_packages=True
        ).button_validate()
        if self.print_package_label:
            self._print_package_label()
        return res

    def _print_package_label(self):
        """Method to be inherited by other modules and allow print the report in
        the background without breaking the chain of returned values.
        For example, you can use base_report_to_printer to send the report directly to
        printer.
        """
        report = (
            self.pick_ids.picking_type_id.report_number_of_packages
            or self.env.ref(
                "delivery_package_number.action_delivery_package_number_report"
            )
        )
        report_action = report.report_action(self.pick_ids)
        report_action.update({"close_on_report_download": True})
        return report_action
