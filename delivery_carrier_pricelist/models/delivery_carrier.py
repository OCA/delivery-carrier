# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("pricelist", "Based on Product Pricelist")],
        ondelete={"pricelist": "set default"},
    )
    invoice_policy = fields.Selection(
        selection_add=[("pricelist", "Delivery Product Price")],
        ondelete={"pricelist": "set default"},
        help="Estimated Cost: the customer will be invoiced the estimated"
        " cost of the shipping.\n"
        "Real Cost: the customer will be invoiced the real cost of the"
        " shipping, the cost of the shipping will be updated on the"
        " SO after the delivery.\n"
        "Delivery Product Price: the customer will be invoiced the price of the "
        "related delivery product based on the pricelist of the sales order. "
        "The provider's cost is ignored.",
    )

    def rate_shipment(self, order):
        if self.invoice_policy == "pricelist":
            # Force computation from pricelist based on invoicing policy
            # Required since core's `rate_shipment` relies on `self.delivery_type`
            # to lookup for the right handler.
            # using a 'temp record' with new() won't work since it has NewId
            # and rate_shipment() compares those
            tmp_type = self.delivery_type
            self.delivery_type = "pricelist"
            result = super().rate_shipment(order)
            self.delivery_type = tmp_type
            return result
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
        product_price = order.pricelist_id._get_product_price(
            self.product_id,
            1.0,
            uom=self.product_id.uom_id,
            date=order.date_order,
        )
        price = order.currency_id._convert(
            product_price,
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
                "error_message": self.env._(
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

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(
            view_id=view_id, view_type=view_type, options=options
        )
        if view.name == "delivery.carrier.form":
            arch = self._fields_view_get_adapt_attrs(arch)
        return arch, view

    @property
    def attrs_list(self):
        return ["invisible", "required", "readonly"]

    def _add_pricelist_domain(
        self,
        doc,
        xpath_expr,
        attrs_key,
        domain_operator="or",
        field_operator="==",
    ):
        """Add the delivery type domain for 'pricelist' in attrs"""

        if attrs_key not in self.attrs_list:
            return

        nodes = doc.xpath(xpath_expr)
        for field in nodes:
            domain = field.attrib.get(attrs_key, "")
            if not domain:
                continue

            delivery_type_domain = f"delivery_type {field_operator} 'pricelist'"
            domain = f"{domain} {domain_operator} {delivery_type_domain}"
            field.set(attrs_key, domain)

    def _fields_view_get_adapt_attrs(self, view_arch):
        """Adapt the attrs of elements in the view with 'pricelist' delivery type"""
        # hide all these fields and buttons for delivery providers which have already
        # an attrs with a domain we can't extend...
        self._add_pricelist_domain(
            view_arch, "//button[@name='toggle_prod_environment']", "invisible"
        )
        self._add_pricelist_domain(
            view_arch, "//button[@name='toggle_debug']", "invisible"
        )
        self._add_pricelist_domain(
            view_arch, "//field[@name='integration_level']", "invisible"
        )
        self._add_pricelist_domain(
            view_arch, "//field[@name='invoice_policy']", "invisible"
        )

        return view_arch
