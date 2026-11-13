# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryDachserCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_es = cls.env.ref("base.es")
        cls.state_sevilla = cls.env["res.country.state"].search(
            [("country_id", "=", cls.country_es.id), ("code", "=", "SE")],
            limit=1,
        )
        if not cls.state_sevilla:
            cls.state_sevilla = cls.env["res.country.state"].create(
                {
                    "name": "Seville",
                    "code": "SE",
                    "country_id": cls.country_es.id,
                }
            )

        cls.wh_partner = cls.env["res.partner"].create(
            {
                "name": "Central Logistics Warehouse Ltd.",
                "street": "Industrial Park North Street 12",
                "city": "Dos Hermanas",
                "zip": "41700",
                "state_id": cls.state_sevilla.id,
                "country_id": cls.country_es.id,
                "phone": "+34955000111",
                "email": "shipping@example.com",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Southern Confectionery Distribution Corporation Ltd.",
                "street": (
                    "Constitution Avenue 125 South Industrial Park "
                    "Warehouse 4 Door B"
                ),
                "city": "Seville",
                "zip": "41001",
                "state_id": cls.state_sevilla.id,
                "country_id": cls.country_es.id,
                "phone": "+34954000111",
                "mobile": "+34600111222",
                "email": "logistics@southernconfectionery.example.com",
                "dachser_partner_id": "87654321",
                "dachser_gln": "8412345678901",
                "dachser_tail_lift": True,
                "dachser_delivery_notice_type": "AS",
            }
        )

        cls.package_type_eu = cls.env.ref(
            "delivery_dachser.stock_package_type_dachser_eu"
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Artisan Chocolate Box 5kg",
                "type": "consu",
                "weight": 5.0,
                "list_price": 45.0,
            }
        )
        cls.shipping_product = cls.env["product.product"].create(
            {
                "name": "Dachser Freight Service Test",
                "type": "service",
                "list_price": 0.0,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Dachser Test Carrier",
                "delivery_type": "dachser",
                "integration_level": "rate_and_ship",
                "product_id": cls.shipping_product.id,
                "prod_environment": False,
                "debug_logging": True,
                "dachser_api_key": "test-api-key-12345",
                "dachser_client_id": "ibm-client-id-001",
                "dachser_forwarder_id": "193",
                "dachser_consignor_id": "12345678",
                "dachser_consignor_gln": "8400000123456",
                "dachser_division": "T",
                "dachser_product_t": "Y",
                "dachser_product_f": "N",
                "dachser_term": "031",
                "dachser_basket": "labelled",
                "dachser_packaging_t": "EU",
                "dachser_packaging_f": "EU",
                "dachser_default_packaging_id": cls.package_type_eu.id,
            }
        )
        cls.carrier_dachser = cls.carrier

        cls.sample_pdf_b64 = base64.b64encode(
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        ).decode("ascii")

        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier
        cls.sale_order.action_confirm()
        cls.sale_order.warehouse_id.partner_id = cls.wh_partner
        cls.picking = cls.sale_order.picking_ids[0]
        cls.picking.carrier_id = cls.carrier
        cls.picking.move_ids.quantity = 20.0
