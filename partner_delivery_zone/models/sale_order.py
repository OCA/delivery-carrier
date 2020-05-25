# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_zone_id = fields.Many2one(
        comodel_name='partner.delivery.zone',
        string="Delivery Zone",
        ondelete='restrict',
        index=True,
    )

    @api.onchange('partner_shipping_id')
    def onchange_partner_shipping_id_delivery_zone(self):
        partner = (self.partner_shipping_id if
                   self.partner_shipping_id.type == 'delivery' else
                   self.partner_shipping_id.commercial_partner_id)
        self.delivery_zone_id = partner.delivery_zone_id
