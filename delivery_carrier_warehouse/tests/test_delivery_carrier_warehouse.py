# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryCarrierWarehouse(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier_product = cls.env["product.product"].create(
            {
                "name": "Delivery Service Product",
                "type": "service",
                "list_price": 5.0,
            }
        )
        cls.delivery_local_delivery = cls.env["delivery.carrier"].create(
            {
                "name": "Local Delivery",
                "fixed_price": 5.0,
                "delivery_type": "fixed",
                "product_id": cls.carrier_product.id,
            }
        )
        cls.free_delivery_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Free Delivery Carrier",
                "fixed_price": 0.0,
                "delivery_type": "fixed",
                "product_id": cls.carrier_product.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner Claim",
                "email": "partner.claim@example.com",
                "phone": "1234567890",
                "type": "contact",
                "property_delivery_carrier_id": cls.delivery_local_delivery.id,
            }
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product",
                "list_price": 30.0,
                "standard_price": 30.0,
                "type": "consu",
                "uom_id": cls.uom_unit.id,
            }
        )
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.warehouse.delivery_carrier_id = cls.free_delivery_carrier

    @classmethod
    def _create_sale_order(cls):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 2
        return sale_form.save()

    def test_warehouse_carrier(self):
        order = self._create_sale_order()
        self.assertEqual(
            self.partner.property_delivery_carrier_id, self.delivery_local_delivery
        )
        action = order.action_open_delivery_wizard()
        default_carrier_id = action["context"]["default_carrier_id"]
        self.assertEqual(default_carrier_id, self.delivery_local_delivery.id)
        self.partner.property_delivery_carrier_id = False
        action = order.action_open_delivery_wizard()
        default_carrier_id = action["context"]["default_carrier_id"]
        self.assertEqual(default_carrier_id, self.free_delivery_carrier.id)
