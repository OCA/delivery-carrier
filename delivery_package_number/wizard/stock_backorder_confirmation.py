# Copyright 2023 Ángel García de la Chica Herrera <angel.garcia@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    number_of_packages = fields.Integer(
        help="Set the number of packages for picking to be validated",
    )
    ask_number_of_packages = fields.Boolean(compute="_compute_ask_number_of_packages")

    @api.depends("pick_ids")
    def _compute_ask_number_of_packages(self):
        for item in self:
            # we use ._origin because if not, a NewId is used for the checks and the returned
            # value of package_ids is wrong.
            item.ask_number_of_packages = bool(
                item.pick_ids.carrier_id and not item.pick_ids._origin.package_ids
            )

    def process(self):
        if self.number_of_packages:
            self.pick_ids.write({"number_of_packages": self.number_of_packages})
        # put context key for avoiding `base_delivery_carrier_label` auto-packaging feature
        return super(
            StockBackorderConfirmation, self.with_context(set_default_package=False)
        ).process()
