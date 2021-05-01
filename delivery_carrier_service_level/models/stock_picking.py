# Copyright 2020 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockPicking(models.Model):
    """Extend stock.picking for carrier service level."""

    _name = "stock.picking"
    _inherit = "stock.picking"

    carrier_service_level_id = fields.Many2one(
        comodel_name="carrier.service.level",
        string="Carrier Service Level",
        domain="[('carrier_id', '=?', carrier_id)]",
    )

    @api.onchange("carrier_id")
    def on_change_carrier_id(self):
        """Set carrier_service_level_id to False"""
        for this in self:
            this.carrier_service_level_id = False
