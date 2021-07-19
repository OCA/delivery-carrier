# Copyright 2020 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPicking(models.Model):
    """Extend stock.picking for carrier service level."""

    _name = "stock.picking"
    _inherit = "stock.picking"

    def _compute_carrier_service_level(self):
        service_level_model = self.env["carrier.service.level"]
        for this in self:
            this.carrier_service_level_id = (
                service_level_model.search(
                    [("carrier_id", "=", this.carrier_id.id)], limit=1,
                )
                if this.carrier_id
                else service_level_model.browse([])
            )

    carrier_service_level_id = fields.Many2one(
        comodel_name="carrier.service.level",
        string="Carrier Service Level",
        domain="[('carrier_id', '=?', carrier_id)]",
        compute="_compute_carrier_service_level",
        inverse=lambda x: None,
    )
