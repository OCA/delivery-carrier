from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestModuleFlow(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )
        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Test Delivery Product",
                "type": "service",
                "list_price": 5.0,
            }
        )
        cls.local_delivery = cls.env["delivery.carrier"].create(
            {
                "name": "Local Delivery",
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
                "fixed_price": 5.0,
            }
        )
        cls.poste_delivery = cls.env["delivery.carrier"].create(
            {
                "name": "The Poste",
                "delivery_type": "base_on_rule",
                "product_id": cls.delivery_product.id,
                "fixed_price": 20.0,
            }
        )
        cls.env["delivery.price.rule"].create(
            {
                "carrier_id": cls.poste_delivery.id,
                "max_value": 5,
                "list_base_price": 20,
            }
        )
        cls.warehouse0 = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse #1",
                "code": "TWH-1",
            }
        )
        cls.warehouse1 = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse #2",
                "code": "TWH-2",
            }
        )
        cls.local_delivery.so_warehouse_id = cls.warehouse0
        cls.poste_delivery.so_warehouse_id = cls.warehouse1
        cls.saleperson_warehouse = cls.env.user._get_default_warehouse_id()

        form = Form(cls.env["sale.order"])
        form.partner_id = cls.partner
        with form.order_line.new() as line:
            line.product_id = cls.product
        cls.sale_order = form.save()

    def _set_shipping_method(self, delivery_method):
        form = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.sale_order.id,
            ),
            view="delivery.choose_delivery_carrier_view_form",
        )
        form.carrier_id = delivery_method
        shipping = form.save()
        shipping.button_confirm()

    def test_sale_order_warehouse_default(self):
        """Test flow when set order warehouse by default"""
        self.assertEqual(
            self.saleperson_warehouse,
            self.sale_order.warehouse_id,
            msg="Order Warehouse must be equal to saleperson default warehouse",
        )

    def test_sale_order_warehouse_custom(self):
        """Test flow when set order warehouse by 'Shipping Method' record"""
        self._set_shipping_method(self.local_delivery)
        self.assertEqual(
            self.warehouse0,
            self.sale_order.warehouse_id,
            msg="Order Warehouse must be equal to 'Test Warehouse #1'",
        )

    def test_sale_order_carrier_id_confirmation(self):
        """Test flow when change 'Shipping Method' after confirmation"""
        self._set_shipping_method(self.local_delivery)
        self.assertEqual(
            self.sale_order.warehouse_id.id,
            self.warehouse0.id,
            msg="Order Warehouse must be equal to 'Test Warehouse #1'",
        )
        self.sale_order.action_confirm()
        self.sale_order.order_line.filtered(
            lambda line: line.is_delivery
        ).qty_invoiced = 0
        self._set_shipping_method(self.poste_delivery)
        self.assertNotEqual(
            self.sale_order.warehouse_id.id,
            self.warehouse1.id,
            msg="Order Warehouse must not be equal to 'Test Warehouse #2'",
        )
        self.assertEqual(
            self.sale_order.warehouse_id.id,
            self.warehouse0.id,
            msg="Order Warehouse must be equal to 'Test Warehouse #1'",
        )
