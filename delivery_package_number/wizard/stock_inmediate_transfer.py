# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    number_of_packages = fields.Integer(
        help="Set the number of packages for this picking(s)",
    )
    ask_number_of_packages = fields.Boolean(compute="_compute_ask_number_of_packages")

    @api.depends("pick_ids")
    def _compute_ask_number_of_packages(self):
        for item in self:
            item.ask_number_of_packages = bool(item.pick_ids.carrier_id)

    def process(self):
        if self.number_of_packages:
            self.pick_ids.write({"number_of_packages": self.number_of_packages})
        return super().process()
