# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_zone_id = fields.Many2one(
        comodel_name="partner.delivery.zone",
        string="Delivery Zone",
        ondelete="restrict",
        compute="_compute_delivery_zone_id",
        store=True,
        readonly=False,
        index=True,
    )

    @api.depends("partner_shipping_id")
    def _compute_delivery_zone_id(self):
        for so in self:
            if so.partner_shipping_id.delivery_zone_id:
                so.delivery_zone_id = so.partner_shipping_id.delivery_zone_id
