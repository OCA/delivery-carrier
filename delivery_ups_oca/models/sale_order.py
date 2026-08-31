# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ups_landed_cost_quote_identifier = fields.Char(
        string="UPS Global Checkout Quote ID",
        help="Quote ID returned by the UPS Global Checkout landed cost calculation. "
        "It must be provided when the shipment is created so UPS can link the "
        "guaranteed duties and taxes to the shipment.",
        readonly=True,
        copy=False,
    )
    ups_landed_cost_amount = fields.Monetary(
        string="UPS Landed Cost",
        help="Total duties, taxes and fees quoted by UPS Global Checkout.",
        currency_field="currency_id",
        readonly=True,
        copy=False,
    )

    def _create_delivery_line(self, carrier, price_unit):
        """Create the standard delivery line and, for UPS Global Checkout, an
        additional line below it carrying the landed cost (duties and taxes)."""
        sol = super()._create_delivery_line(carrier, price_unit)
        if carrier.delivery_type == "ups":
            self._ups_sync_landed_cost_line(carrier, sol)
        return sol

    def _ups_sync_landed_cost_line(self, carrier, delivery_sol):
        """Create/refresh the UPS landed cost order line just below the delivery
        line.

        The line is only created when a tariff product is configured on the
        carrier and a landed cost has been quoted for the order. Any existing
        landed cost line is removed first to avoid duplicates on refresh.
        """
        self.ensure_one()
        self._ups_remove_landed_cost_line()
        product = carrier.ups_landed_cost_product_id
        if not (
            product
            and self.ups_landed_cost_quote_identifier
            and self.ups_landed_cost_amount
        ):
            return self.env["sale.order.line"]
        taxes = product.taxes_id._filter_taxes_by_company(self.company_id)
        if self.fiscal_position_id:
            taxes = self.fiscal_position_id.map_tax(taxes)
        values = {
            "order_id": self.id,
            "name": _("UPS Duties & Taxes (Global Checkout)"),
            "product_id": product.id,
            "product_uom_qty": 1,
            "product_uom": product.uom_id.id,
            "price_unit": self.ups_landed_cost_amount,
            "tax_id": [(6, 0, taxes.ids)],
            "is_ups_landed_cost": True,
            "sequence": delivery_sol.sequence + 1 if delivery_sol else 999,
        }
        return self.env["sale.order.line"].sudo().create(values)

    def _ups_remove_landed_cost_line(self):
        """Remove the UPS landed cost lines that have not been invoiced yet."""
        lines = self.order_line.filtered(
            lambda x: x.is_ups_landed_cost and x.qty_invoiced == 0
        )
        if lines:
            lines.unlink()

    def _remove_delivery_line(self):
        """Also remove the UPS landed cost line when the delivery line is
        removed (e.g. carrier change/removal)."""
        res = super()._remove_delivery_line()
        self._ups_remove_landed_cost_line()
        return res

    def _get_update_prices_lines(self):
        """Exclude the UPS landed cost line from pricelist recomputation so its
        quoted amount is not overwritten by the tariff product's list price."""
        lines = super()._get_update_prices_lines()
        return lines.filtered(lambda line: not line.is_ups_landed_cost)
