# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import base64

# A one-page BLANK PDF, kept as a literal so the fixture does not depend on which
# pypdf backend the running Odoo picked up.
MINIMAL_PDF = base64.b64decode(
    "JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMg"
    "WyAzIDAgUiBdCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9Qcm9kdWNlciAoT2RvbykKL0NyZWF0"
    "b3IgKE9kb28pCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9QYWdlCi9QYXJlbnQgMSAw"
    "IFIKL1Jlc291cmNlcyA8PAo+PgovTWVkaWFCb3ggWyAwIDAgMjAwIDIwMCBdCj4+CmVuZG9i"
    "ago0IDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAxIDAgUgo+PgplbmRvYmoKeHJl"
    "ZgowIDUKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDE1IDAwMDAwIG4gCjAwMDAwMDAw"
    "NzQgMDAwMDAgbiAKMDAwMDAwMDEyOCAwMDAwMCBuIAowMDAwMDAwMjE4IDAwMDAwIG4gCnRy"
    "YWlsZXIKPDwKL1NpemUgNQovUm9vdCA0IDAgUgovSW5mbyAyIDAgUgo+PgpzdGFydHhyZWYK"
    "MjY3CiUlRU9GCg=="
)


class SendcloudSaleOrderMixin:
    """The sale order the Sendcloud tests ship.

    Demo data is no longer installed by default since 19.0, so the order is
    built here instead of copying `sale.sale_order_1`.
    """

    def _setup_sendcloud_accounting(self):
        """A chart of accounts, for the tests that invoice the order.

        Loaded on demand rather than for the whole class, because it also sets
        the company's currency and fiscal country, which the other tests do
        without.
        """
        company = self.env.company
        journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", company.id)], limit=1
        )
        if not journal:
            self.env["account.chart.template"].try_loading(
                "generic_coa", company=company, install_demo=False
            )

    def _setup_sendcloud_sender_address(self):
        """Give the company a full address.

        Sendcloud ships from the warehouse address, and the goods take their
        country of origin from it, so the tests that ship outside the EU need
        it filled in.
        """
        self.env.company.partner_id.write(
            {
                "street": "250 Executive Park Blvd",
                "city": "San Francisco",
                "state_id": self.env.ref("base.state_us_5").id,
                "zip": "94134",
                "country_id": self.env.ref("base.us").id,
                "phone": "+1 555 0100",
            }
        )

    def _create_sendcloud_partner(self):
        """A customer outside the EU, which the customs tests need."""
        return self.env["res.partner"].create(
            {
                "name": "Acme Corporation",
                "street": "77 Santa Barbara Rd",
                "city": "Pleasant Hill",
                "state_id": self.env.ref("base.state_us_5").id,
                "zip": "94523",
                "country_id": self.env.ref("base.us").id,
                "email": "acme_corp@yourcompany.example.com",
                "phone": "(603)-996-3829",
            }
        )

    def _create_sendcloud_sale_order(self, partner=None):
        """An order of deliverable goods, light enough to stay under the
        weight limit of every shipping method the cassettes return."""
        partner = partner or self._create_sendcloud_partner()
        lines = [("Office Chair", 70.0, 2), ("Office Lamp", 40.0, 5)]
        order_lines = []
        for name, price, qty in lines:
            product = self.env["product.product"].create(
                {"name": name, "type": "consu", "weight": 0.01, "list_price": price}
            )
            order_lines.append(
                (0, 0, {"product_id": product.id, "product_uom_qty": qty})
            )
        return self.env["sale.order"].create(
            {"partner_id": partner.id, "order_line": order_lines}
        )

    def _create_sendcloud_picking(self, partner=None):
        """An outgoing transfer to hang parcels and labels on."""
        partner = partner or self._create_sendcloud_partner()
        picking_type = self.env.ref("stock.picking_type_out")
        return self.env["stock.picking"].create(
            {
                "partner_id": partner.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": partner.property_stock_customer.id,
            }
        )
