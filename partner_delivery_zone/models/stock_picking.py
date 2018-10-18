# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_zone_id = fields.Many2one(
        comodel_name="partner.delivery.zone",
        string="Delivery Zone",
        index=True,
    )

    @api.onchange('partner_id')
    def onchange_partner_id_zone(self):
        if self.partner_id.delivery_zone_id:
            self.delivery_zone_id = self.partner_id.delivery_zone_id
