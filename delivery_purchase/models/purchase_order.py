# Copyright 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier", string="Delivery Method",
    )
    delivery_price = fields.Float()

    @api.onchange("partner_id")
    def onchange_partner_id_delivery_purchase(self):
        if self.partner_id.property_delivery_carrier_id:
            self.carrier_id = self.partner_id.property_delivery_carrier_id.id

    @api.onchange("order_line", "amount_total", "carrier_id")
    def get_delivery_cost(self):
        if self.carrier_id:
            self.delivery_price = self.carrier_id.purchase_rate_shipment(self)["price"]

    @api.model
    def _prepare_picking(self):
        res = super()._prepare_picking()
        if self.carrier_id:
            res["carrier_id"] = self.carrier_id.id
        return res
