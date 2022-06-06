# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

from odoo.addons.base.models.ir_ui_view import (
    transfer_modifiers_to_node,
    transfer_node_to_modifiers,
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    invoice_policy = fields.Selection(
        selection_add=[("base_on_rule", "Rule Cost")],
        ondelete={"base_on_rule": "set default"},
        help="Estimated Cost: the customer will be invoiced the estimated"
        " cost of the shipping.\n"
        "Real Cost: the customer will be invoiced the real cost of the"
        " shipping, the cost of the shipping will be updated on the"
        " SO after the delivery.\n"
        "Rule Cost: the customer will be invoiced the price "
        "calculated with the rules table. The provider's "
        "cost is ignored.",
    )

    def rate_shipment(self, order):
        if self.invoice_policy == "base_on_rule":
            current_type = self.delivery_type
            # force computation from base_on_rule when the invoicing policy says so
            self.delivery_type = "base_on_rule"
            result = super().rate_shipment(order)
            self.delivery_type = current_type
            return result
        else:
            return super().rate_shipment(order)

    def send_shipping(self, pickings):
        result = super().send_shipping(pickings)
        if self.invoice_policy == "base_on_rule":
            # force computation from base_on_rule when the invoicing policy says so
            rates = self.base_on_rule_send_shipping(pickings)
            for index, rate in enumerate(rates):
                result[index]["exact_price"] = rate["exact_price"]
        return result

    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if result["name"] == "delivery.carrier.form":
            result["arch"] = self._fields_view_get_adapt_attrs(result["arch"])
        return result

    def _add_rule_domain(self, doc, xpath_expr, attrs_key):
        nodes = doc.xpath(xpath_expr)
        for field in nodes:
            attrs = safe_eval(field.attrib.get("attrs", "{}"))
            if not attrs[attrs_key]:
                continue
            invisible_domain = expression.AND(
                [attrs[attrs_key], [("invoice_policy", "!=", "base_on_rule")]]
            )
            attrs[attrs_key] = invisible_domain
            field.set("attrs", str(attrs))
            modifiers = {}
            transfer_node_to_modifiers(
                field, modifiers, self.env.context, current_node_path=["tree"]
            )
            transfer_modifiers_to_node(modifiers, field)

    def _fields_view_get_adapt_attrs(self, view_arch):
        doc = etree.XML(view_arch)
        self._add_rule_domain(doc, "//page[@name='pricing']", "invisible")
        self._add_rule_domain(doc, "//group[@name='general']", "invisible")
        new_view = etree.tostring(doc, encoding="unicode")
        return new_view
