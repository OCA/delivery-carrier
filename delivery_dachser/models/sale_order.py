# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    dachser_estimated_cost = fields.Float(
        string="Internal Estimated Dachser Cost (€)",
        digits="Product Price",
        copy=False,
        help=(
            "Real estimated Dachser shipping cost (preserved internally even "
            "when shipping is free for the customer)."
        ),
    )
    dachser_quotation_id = fields.Char(
        string="Dachser Quotation ID",
        copy=False,
    )
    dachser_chargeable_weight = fields.Float(
        string="Dachser Chargeable Weight (kg)",
        copy=False,
    )
    dachser_rate_breakdown = fields.Text(
        string="Dachser Tariff Breakdown",
        copy=False,
    )

    def _get_estimated_weight(self):
        """Extend estimated order weight calculation to support packaging weights
        (`_get_packaging_unit_weight`) when `product_id.weight` is 0.
        """
        self.ensure_one()
        weight = super()._get_estimated_weight()
        if weight > 0:
            return weight
        custom_weight = 0.0
        for line in self.order_line.filtered(
            lambda ol: not ol.is_delivery
            and not ol.display_type
            and ol.product_id.type in ("consu", "product")
        ):
            if hasattr(line.product_id, "_get_packaging_unit_weight"):
                pkg_w = line.product_id._get_packaging_unit_weight(
                    packaging=line.product_packaging_id,
                    weight_type="gross",
                )
                custom_weight += (pkg_w or 0.0) * line.product_uom_qty
        return custom_weight

    def _create_delivery_line(self, carrier, price_unit):
        """When creating the delivery line on the sale order, if the carrier is
        Dachser and `sale_margin` (`purchase_price` on `sale.order.line`) is
        installed, record the real estimated cost (`dachser_estimated_cost`)
        as the line cost even if the customer pays 0 €.
        """
        sol = super()._create_delivery_line(carrier, price_unit)
        if (
            sol
            and carrier.delivery_type == "dachser"
            and self.dachser_estimated_cost > 0
            and "purchase_price" in sol._fields
        ):
            sol.purchase_price = self.dachser_estimated_cost
        return sol


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    is_dachser_carrier = fields.Boolean(
        string="Is Dachser",
        compute="_compute_is_dachser_carrier",
    )
    dachser_estimated_cost = fields.Float(
        string="Internal Dachser Cost (€)",
        digits="Product Price",
        readonly=True,
    )
    dachser_chargeable_weight = fields.Float(
        string="Chargeable Weight (kg)",
        readonly=True,
    )
    dachser_rate_breakdown = fields.Text(
        string="Dachser Tariff Breakdown",
        readonly=True,
    )

    @api.depends("carrier_id", "carrier_id.delivery_type")
    def _compute_is_dachser_carrier(self):
        for rec in self:
            rec.is_dachser_carrier = bool(
                rec.carrier_id and rec.carrier_id.delivery_type == "dachser"
            )

    def _get_delivery_rate(self):
        res = super()._get_delivery_rate()
        if (
            self.carrier_id
            and self.carrier_id.delivery_type == "dachser"
            and self.order_id
        ):
            self.dachser_estimated_cost = self.order_id.dachser_estimated_cost
            self.dachser_chargeable_weight = self.order_id.dachser_chargeable_weight
            self.dachser_rate_breakdown = self.order_id.dachser_rate_breakdown
        else:
            self.dachser_estimated_cost = 0.0
            self.dachser_chargeable_weight = 0.0
            self.dachser_rate_breakdown = False
        return res
