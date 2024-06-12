# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_amount_total_without_delivery(self):
        atwd = super()._compute_amount_total_without_delivery()
        delivery_collection_cost = sum(
            line.price_total for line in self.order_line if line.is_delivery_collection
        )
        if delivery_collection_cost:
            delivery_collection_cost = self.env["delivery.carrier"]._compute_currency(
                self, delivery_collection_cost, "pricelist_to_company"
            )
        return atwd - delivery_collection_cost

    @api.onchange("order_line", "partner_id", "partner_shipping_id")
    def onchange_order_line(self):
        super().onchange_order_line()

        delivery_collection_line = self.order_line.filtered("is_delivery_collection")
        if delivery_collection_line:
            self.recompute_delivery_price = True

    def _get_update_prices_lines(self):
        lines = super()._get_update_prices_lines()
        return lines.filtered(lambda line: not line.is_delivery_collection)

    def _remove_delivery_line(self):
        delivery_collection_line = self.env["sale.order.line"].search(
            [("order_id", "in", self.ids), ("is_delivery_collection", "=", True)]
        )
        if delivery_collection_line:
            to_delete = delivery_collection_line.filtered(lambda x: x.qty_invoiced == 0)
            if not to_delete:
                raise UserError(
                    _(
                        "You can not update the shipping costs on an order where it "
                        "was already invoiced!\n\nThe following delivery collection "
                        "lines (product, invoiced quantity and price) have already "
                        "been processed:\n\n"
                    )
                    + "\n".join(
                        [
                            "- %s: %s x %s"
                            % (
                                line.product_id.with_context(
                                    display_default_code=False
                                ).display_name,
                                line.qty_invoiced,
                                line.price_unit,
                            )
                            for line in delivery_collection_line
                        ]
                    )
                )
            to_delete.unlink()
        return super()._remove_delivery_line()

    def _create_delivery_line(self, carrier, price_unit):
        """
        Method adapted from `delivery`,
        applied to `collection_product_id` instead of `product_id`
        """
        delivery_sol = super()._create_delivery_line(carrier, price_unit)
        if not carrier.collection_product_id:
            return delivery_sol
        collection_price_unit = carrier.get_collection_price_unit(self)
        if not collection_price_unit:
            return delivery_sol
        SaleOrderLine = self.env["sale.order.line"]
        context = {}
        if self.partner_id:
            # set delivery detail in the customer language
            # used in local scope translation process
            context["lang"] = self.partner_id.lang
            carrier = carrier.with_context(lang=self.partner_id.lang)

        # Apply fiscal position
        taxes = carrier.collection_product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id
        )
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(
                taxes, carrier.collection_product_id, self.partner_id
            ).ids

        # Create the sales order line
        values = {
            "order_id": self.id,
            "name": carrier.collection_product_id.description_sale
            or carrier.collection_product_id.name,
            "product_uom_qty": 1,
            "product_uom": carrier.collection_product_id.uom_id.id,
            "product_id": carrier.collection_product_id.id,
            "tax_id": [(6, 0, taxes_ids)],
            "is_delivery_collection": True,
            "price_unit": collection_price_unit,
        }

        if self.order_line:
            values["sequence"] = delivery_sol.sequence
            delivery_sol.sequence += 1
        SaleOrderLine.sudo().create(values)
        del context
        # return original sol for compatibility
        return delivery_sol

    @api.depends("order_line.is_delivery_collection")
    def _get_invoice_status(self):
        super()._get_invoice_status()
        for order in self:
            if order.invoice_status in ["no", "invoiced"]:
                continue
            order_lines = order.order_line.filtered(
                lambda x: not x.is_delivery_collection
                and not x.is_delivery
                and not x.is_downpayment
                and not x.display_type
            )
            if all(
                line.product_id.invoice_policy == "delivery"
                and line.invoice_status == "no"
                for line in order_lines
            ):
                order.invoice_status = "no"
