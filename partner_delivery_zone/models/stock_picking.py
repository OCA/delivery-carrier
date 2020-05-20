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
        partner = (self.partner_id if
                   self.partner_id.type == 'delivery' else
                   self.partner_id.commercial_partner_id)
        self.delivery_zone_id = partner.delivery_zone_id
