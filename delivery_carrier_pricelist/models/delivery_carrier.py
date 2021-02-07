# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import _, fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

from odoo.addons.base.models.ir_ui_view import (
    transfer_modifiers_to_node,
    transfer_node_to_modifiers,
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("pricelist", "Based on Product Pricelist")],
        ondelete={"pricelist": "set default"},
    )
    invoice_policy = fields.Selection(
        selection_add=[("pricelist", "Pricelist Cost")],
        ondelete={"pricelist": "set default"},
        help="Estimated Cost: the customer will be invoiced the estimated"
        " cost of the shipping.\n"
        "Real Cost: the customer will be invoiced the real cost of the"
        " shipping, the cost of the shipping will be updated on the"
        " SO after the delivery.\n"
        "Pricelist Cost: the customer will be invoiced the price of the "
        "product based on the pricelist of the sales order. The provider's "
        "cost is ignored.",
    )

    def rate_shipment(self, order):
        if self.invoice_policy == "pricelist":
            current_type = self.delivery_type
            # force computation from pricelist when the invoicing policy says
            # so
            self.delivery_type = "pricelist"
            result = super().rate_shipment(order)
            self.delivery_type = current_type
            return result
        else:
            return super().rate_shipment(order)

    def send_shipping(self, pickings):
        result = super().send_shipping(pickings)
        if self.invoice_policy == "pricelist":
            # force computation from pricelist when the invoicing policy says
            # so
            rates = self.pricelist_send_shipping(pickings)
            for index, rate in enumerate(rates):
                result[index]["exact_price"] = rate["exact_price"]
        return result

    def _pricelist_get_price(self, order):
        product = self.product_id.with_context(
            pricelist=order.pricelist_id.id,
            partner=order.partner_id,
            quantity=1,
            date=order.date_order,
            uom=self.product_id.uom_id.id,
        )
        price = order.currency_id._convert(
            product.price,
            order.company_id.currency_id,
            order.company_id,
            order.date_order or fields.Date.today(),
        )
        return price

    def pricelist_rate_shipment(self, order):
        carrier = self._match_address(order.partner_shipping_id)
        if not carrier:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "Error: this delivery method is not available for this address."
                ),
                "warning_message": False,
            }
        price = self._pricelist_get_price(order)
        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }

    def pricelist_send_shipping(self, pickings):
        res = []
        for picking in pickings:
            carrier = picking.carrier_id
            sale = picking.sale_id
            price = carrier._pricelist_get_price(sale) if sale else 0.0
            res = res + [{"exact_price": price, "tracking_number": False}]
        return res

    def pricelist_get_tracking_link(self, picking):
        return False

    def pricelist_cancel_shipment(self, pickings):
        raise NotImplementedError()

    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if result["name"] == "delivery.carrier.form":
            result["arch"] = self._fields_view_get_adapt_attrs(result["arch"])
        return result

    def _add_pricelist_domain(
        self,
        doc,
        xpath_expr,
        attrs_key,
        domain_operator=expression.OR,
        field_operator="=",
    ):
        """Add the delivery type domain for 'pricelist' in attrs"""
        nodes = doc.xpath(xpath_expr)
        for field in nodes:
            attrs = safe_eval(field.attrib.get("attrs", "{}"))
            if not attrs[attrs_key]:
                continue

            invisible_domain = domain_operator(
                [attrs[attrs_key], [("delivery_type", field_operator, "pricelist")]]
            )
            attrs[attrs_key] = invisible_domain
            field.set("attrs", str(attrs))
            modifiers = {}
            transfer_node_to_modifiers(
                field, modifiers, self.env.context, current_node_path=["tree"]
            )
            transfer_modifiers_to_node(modifiers, field)

    def _fields_view_get_adapt_attrs(self, view_arch):
        """Adapt the attrs of elements in the view with 'pricelist' delivery type"""
        doc = etree.XML(view_arch)
        # hide all these fields and buttons for delivery providers which have already
        # an attrs with a domain we can't extend...
        self._add_pricelist_domain(
            doc, "//button[@name='toggle_prod_environment']", "invisible"
        )
        self._add_pricelist_domain(doc, "//button[@name='toggle_debug']", "invisible")
        self._add_pricelist_domain(
            doc, "//field[@name='integration_level']", "invisible"
        )
        self._add_pricelist_domain(doc, "//field[@name='invoice_policy']", "invisible")

        new_view = etree.tostring(doc, encoding="unicode")
        return new_view
