# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockNumberPackageValidateWiz(models.TransientModel):
    _name = "stock.number.package.validate.wizard"
    _description = "Wizard to force set number of pickings when validate"

    pick_ids = fields.Many2many("stock.picking", "stock_picking_number_package_rel")
    number_of_packages = fields.Integer(
        help="Set the number of packages for this picking(s)",
    )
    stock_number_package_validation_line_ids = fields.One2many(
        comodel_name="stock.number.package.validate.line.wizard",
        inverse_name="wiz_id",
        compute="_compute_stock_number_package_validation_line_ids",
        readonly=False,
        store=True,
    )
    print_package_label = fields.Boolean(
        compute="_compute_print_package_label", readonly=False, store=True
    )

    @api.depends("pick_ids")
    def _compute_print_package_label(self):
        for item in self:
            item.print_package_label = item.pick_ids.picking_type_id.print_label

    @api.depends("pick_ids")
    def _compute_stock_number_package_validation_line_ids(self):
        for wiz in self:
            if len(wiz.pick_ids) <= 1:
                wiz.stock_number_package_validation_line_ids = False
            else:
                wiz.stock_number_package_validation_line_ids = [
                    fields.Command.create({"picking_id": picking.id})
                    for picking in wiz.pick_ids
                ]

    def process(self):
        if self.number_of_packages:
            self.pick_ids.write({"number_of_packages": self.number_of_packages})
        # put context key for avoiding `base_delivery_carrier_label` auto-packaging feature
        self.pick_ids.with_context(
            set_default_package=False, bypass_set_number_of_packages=True
        ).button_validate()
        if self.print_package_label:
            return self._print_package_label()

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


class StockNumberPackageValidateLineWizLine(models.TransientModel):
    _name = "stock.number.package.validate.line.wizard"
    _description = "Stock Number Package Lines Wizard"

    wiz_id = fields.Many2one(
        comodel_name="stock.number.package.validate.wizard", readonly=True
    )
    picking_id = fields.Many2one(comodel_name="stock.picking")
    number_of_packages = fields.Integer(
        related="picking_id.number_of_packages", readonly=False
    )
