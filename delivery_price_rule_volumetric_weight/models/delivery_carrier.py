# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _get_price_available(self, order):
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        volumetric_weight = 0
        for line in order.order_line.filtered(
            lambda x: x.state != "cancel" and x.product_id and not x.is_delivery
        ):
            qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )
            volumetric_weight += (line.product_id.volumetric_weight or 0.0) * qty
        _self = self.with_context(volumetric_weight=volumetric_weight)
        return super(DeliveryCarrier, _self)._get_price_available(order)

    def _get_price_dict(self, total, weight, volume, quantity):
        res = super()._get_price_dict(total, weight, volume, quantity)
        res["volumetric_weight"] = self.env.context.get("volumetric_weight", 0)
        return res
