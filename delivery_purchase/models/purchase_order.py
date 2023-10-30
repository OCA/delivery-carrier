# Copyright 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        compute="_compute_carrier_id",
        store=True,
        readonly=False,
        string="Delivery Method",
    )
    delivery_price = fields.Float(
        compute="_compute_delivery_price", store=True, readonly=False
    )

    @api.depends("partner_id")
    def _compute_carrier_id(self):
        for item in self:
            carrier = item.partner_id.property_delivery_carrier_id or False
            item.carrier_id = carrier

    @api.depends("order_line", "amount_total", "carrier_id")
    def _compute_delivery_price(self):
        for item in self.filtered(lambda x: x.carrier_id):
            item.delivery_price = item.carrier_id.purchase_rate_shipment(self)["price"]

    @api.model
    def _prepare_picking(self):
        res = super()._prepare_picking()
        if self.carrier_id:
            res["carrier_id"] = self.carrier_id.id
        return res
