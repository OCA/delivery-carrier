from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestModuleFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.local_delivery = cls.env.ref(
            "delivery.delivery_local_delivery", raise_if_not_found=False
        )
        cls.poste_delivery = cls.env.ref(
            "delivery.delivery_carrier", raise_if_not_found=False
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
        cls.local_delivery.write({"so_warehouse_id": cls.warehouse0.id})
        cls.poste_delivery.write({"so_warehouse_id": cls.warehouse1.id})
        cls.saleperson_warehouse = cls.env.user._get_default_warehouse_id()

        form = Form(
            cls.env["sale.order"],
        )
        form.partner_id = cls.env.ref("base.res_partner_2", raise_if_not_found=False)
        with form.order_line.new() as line:
            line.product_id = cls.env.ref(
                "product.product_product_25", raise_if_not_found=False
            )
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
