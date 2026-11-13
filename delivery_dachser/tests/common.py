# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.tests import Form, TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestDeliveryDachserCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))

        cls.country_es = cls.env.ref("base.es")
        cls.country_de = cls.env.ref("base.de")
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
                "name": "Agruconf Central Logistics Ltd.",
                "street": "Industrial Park North Street 12",
                "city": "Dos Hermanas",
                "zip": "41700",
                "state_id": cls.state_sevilla.id,
                "country_id": cls.country_es.id,
                "phone": "+34955000111",
                "email": "shipping@agruconf.es",
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

        cls.package_type_eu = cls.env["stock.package.type"].create(
            {
                "name": "Dachser Europallet Test",
                "package_carrier_type": "dachser",
                "dachser_packaging_code": "EU",
                "packaging_length": 120,
                "width": 80,
                "height": 120,
                "base_weight": 25.0,
                "max_weight": 800.0,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Artisan Chocolate Box 5kg",
                "type": "consu",
                "weight": 5.0,
                "list_price": 45.0,
            }
        )
        cls.delivery_product = cls.env["product.product"].create(
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
                "product_id": cls.delivery_product.id,
                "prod_environment": False,
                "debug_logging": True,
                "dachser_api_url": "https://api-gateway.dachser.com/rest/v2",
                "dachser_api_key": "test-api-key-12345",
                "dachser_api_key_test": "test-api-key-12345",
                "dachser_api_key_prod": "prod-api-key-67890",
                "dachser_client_id": "ibm-client-id-001",
                "dachser_forwarder_id": "193",
                "dachser_consignor_id": "12345678",
                "dachser_consignor_gln": "8400000123456",
                "dachser_division": "T",
                "dachser_product_t": "Y",
                "dachser_product_f": "N",
                "dachser_product": "Y",
                "dachser_term": "031",
                "dachser_basket": "labelled",
                "dachser_packaging_t": "EU",
                "dachser_packaging_f": "EU",
                "dachser_default_packaging_id": cls.package_type_eu.id,
                "dachser_default_package_type_id": cls.package_type_eu.id,
                "dachser_default_packaging_code": "EU",
                "dachser_rate_mode": "api_with_fallback",
                "dachser_volumetric_factor": 333.0,
                "dachser_ldm_factor": 1850.0,
                "dachser_fuel_surcharge_pct": 5.0,
                "dachser_tail_lift_surcharge": 12.0,
                "dachser_notice_surcharge": 3.5,
            }
        )
        # Keep OCA alias for compatibility
        cls.carrier_dachser = cls.carrier

        cls.tariff_rule = cls.env["dachser.tariff.rule"].create(
            {
                "name": "Spain Seville / Madrid Excess Kg",
                "carrier_id": cls.carrier.id,
                "sequence": 10,
                "country_ids": [(6, 0, [cls.country_es.id])],
                "state_ids": [(6, 0, [cls.state_sevilla.id])],
                "zip_prefixes": "41, 28",
                "rate_type": "per_excess_kg",
                "base_price": 20.0,
                "included_weight": 50.0,
                "price_per_kg": 0.25,
                "min_charge": 20.0,
                "fuel_surcharge_pct": 5.0,
            }
        )

        cls.sample_pdf_b64 = base64.b64encode(
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        ).decode("ascii")

        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
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
