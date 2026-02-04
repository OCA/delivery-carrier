# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryDachser(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 0.0}
        )
        cls.carrier_dachser = cls.env["delivery.carrier"].create(
            {
                "name": "Dachser",
                "delivery_type": "dachser",
                "product_id": cls.shipping_product.id,
                "debug_logging": True,
                "prod_environment": False,
                # You can define an api_key to test the test properly, there is
                # no public one that does not expire.
                "dachser_api_key": False,
                "dachser_division": "T",
                "dachser_product_t": "Y",
                "dachser_term": "031",
                "dachser_packaging_t": "EU",
                "dachser_default_packaging_id": cls.env.ref(
                    "delivery_dachser.stock_package_dachser_default"
                ).id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "consu", "name": "Test product"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Madrid",
                "zip": "28001",
                "email": "odoo@test.com",
                "street": "Calle de La Rua, 3",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_dachser
        cls.sale_order.action_confirm()
        # Ensure shipper address
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_ids.quantity = 20

    def test_01_dachser_order_rate_shipment(self):
        if not self.carrier_dachser.dachser_api_key:
            self.skipTest("Without Dachser Api Key")
        res = self.sale_order.action_open_delivery_wizard()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})
        wizard.display_price = 0
        wizard.carrier_id = self.carrier_dachser
        wizard.update_price()
        self.assertNotEqual(wizard.display_price, 0)

    def test_02_dachser_picking_confirm_simple(self):
        if not self.carrier_dachser.dachser_api_key:
            self.skipTest("Without Dachser Api Key")
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertEqual(self.picking.tracking_state_history, "sent")

    def test_03_dachser_picking_confirm_simple(self):
        if not self.carrier_dachser.dachser_api_key:
            self.skipTest("Without Dachser Api Key")
        self.picking.carrier_tracking_ref = "test"
        self.picking.delivery_state = False
        self.picking.tracking_state_update()
        self.assertTrue(self.picking.delivery_state)
        self.assertTrue(self.picking.tracking_state_history)

    def test_04_dachser_picking_cancel_shipment(self):
        if not self.carrier_dachser.dachser_api_key:
            self.skipTest("Without Dachser Api Key")
        self.picking.carrier_tracking_ref = "test"
        error_msg = (
            "It is not possible to cancel a shipment because it has already been sent."
        )
        with self.assertRaisesRegex(UserError, error_msg):
            self.picking.cancel_shipment()
