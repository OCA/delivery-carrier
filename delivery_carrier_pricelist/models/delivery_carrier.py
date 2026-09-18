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
        # OVERRIDE: in case ``invoice_policy`` is set as "pricelist", we want to use
        # method ``pricelist_rate_shipment`` to retrieve the proper prices. However,
        # Odoo uses ``getattr(self, '%s_rate_shipment' % self.delivery_type)`` in its
        # base method ``rate_shipment()`` to lookup which function to use, so we
        # temporarily change the ``delivery_type`` if needed.

        # TODO: I would propose the addition of _rate_shipment_get_handler
        # instead of using getattr directly.
        # This way, in v19 or 20 we can get rid of this hack.
        # Also note that some specific carrier implementation
        # rely on computed fields depending on delivery_type
        # so we might trigger unnecessary changes w/ this patchy approach.

        # Quick check: if the invoice policy is not "pricelist", or the delivery type is
        # already set to "pricelist", we don't have to do anything
        if self.invoice_policy != "pricelist" or self.delivery_type == "pricelist":
            return super().rate_shipment(order)

        # Use ``sudo()`` to prevent ``AccessError`` when updating the delivery type
        delivery_type = self.delivery_type
        self.sudo().delivery_type = "pricelist"
        result = super().rate_shipment(order)
        self.sudo().delivery_type = delivery_type
        return result

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
