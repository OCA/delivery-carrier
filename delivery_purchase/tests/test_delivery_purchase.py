# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryPurchaseBase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.delivery_product = cls.env["product.product"].create(
            {"name": "Delivery test product"}
        )
        cls.carrier_fixed = cls.env["delivery.carrier"].create(
            {
                "product_id": cls.delivery_product.id,
                "delivery_type": "fixed",
                "fixed_price": 20,
                "name": "Carrier Test",
            }
        )
        cls.carrier_rules = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier Rule",
                "product_id": cls.delivery_product.id,
                "delivery_type": "base_on_rule",
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "weight",
                            "operator": ">",
                            "max_value": 5,
                            "list_base_price": "30",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "variable": "weight",
                            "operator": "<=",
                            "max_value": 5,
                            "list_base_price": "10",
                        },
                    ),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "property_delivery_carrier_id": cls.carrier_fixed.id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        purchase_form = Form(cls.env["purchase.order"])
        purchase_form.partner_id = cls.partner
        with purchase_form.order_line.new() as purchase_line_form:
            purchase_line_form.product_id = cls.product
            purchase_line_form.price_unit = 1
        cls.purchase = purchase_form.save()
        cls.purchase_line = cls.purchase.order_line

    def _action_picking_validate(self, picking):
        res = picking.button_validate()
        model = self.env[res["res_model"]].with_context(**res["context"])
        model.create({}).process()


class TestDeliveryPurchase(TestDeliveryPurchaseBase):
    def test_onchange_partner_id(self):
        self.assertEqual(self.purchase.carrier_id, self.carrier_fixed)

    def test_purchase_delivery_line_invoice_status(self):
        self.purchase.button_confirm()
        self.assertEqual(self.purchase.invoice_status, "no")
        self.purchase._create_delivery_line(
            self.purchase.carrier_id, self.purchase.delivery_price
        )
        delivery_line = self.purchase.order_line.filtered(lambda x: x.is_delivery)
        self.assertEqual(delivery_line.qty_to_invoice, 0)
        self.assertEqual(self.purchase.invoice_status, "no")
        picking = self.purchase.picking_ids
        picking.carrier_id = False
        self._action_picking_validate(picking)
        self.assertEqual(delivery_line.qty_to_invoice, 1)
        self.assertEqual(self.purchase.invoice_status, "to invoice")

    def test_delivery_purchase(self):
        self.assertEqual(self.purchase.delivery_price, 20)
        self.purchase.carrier_id = self.carrier_rules.id
        self.assertEqual(self.purchase.delivery_price, 10)
        self.purchase_line.product_id.weight = 8
        # Change price unit to amount_total change call compute
        self.purchase_line.price_unit = 2
        self.assertEqual(self.purchase.delivery_price, 30)

    def test_picking_carrier_01(self):
        self.assertEqual(self.purchase.delivery_price, 20)
        self.purchase.button_confirm()
        picking = self.purchase.picking_ids
        self.assertEqual(picking.carrier_id, self.carrier_fixed)
        self.assertEqual(picking.carrier_price, 20)
        picking.carrier_id = self.carrier_rules.id
        self._action_picking_validate(picking)
        self.assertEqual(picking.carrier_price, 10)
        self.assertEqual(
            len(self.purchase.order_line.filtered(lambda x: x.is_delivery)), 1
        )
        self.assertEqual(self.purchase.delivery_price, 10)

    def test_picking_carrier_02(self):
        self.purchase.delivery_price = 0
        self.purchase.button_confirm()
        picking = self.purchase.picking_ids
        picking.carrier_id = self.carrier_fixed
        self._action_picking_validate(picking)
        self.assertEqual(picking.carrier_price, 20)
        delivery_line = self.purchase.order_line.filtered(lambda x: x.is_delivery)
        self.assertEqual(delivery_line.delivery_picking_orig_id, picking)
        self.assertEqual(self.purchase.delivery_price, 20)

    def test_picking_carrier_multi(self):
        self.purchase.order_line.product_qty = 2
        self.purchase.button_confirm()
        picking = self.purchase.picking_ids
        picking.carrier_id = self.carrier_fixed
        for move in picking.move_ids_without_package:
            move.quantity_done = 1
        res = picking.button_validate()
        model = self.env[res["res_model"]].with_context(**res["context"])
        model.create({}).process_cancel_backorder()
        self.assertEqual(picking.carrier_price, 20)
        delivery_line = self.purchase.order_line.filtered(lambda x: x.is_delivery)
        self.assertEqual(delivery_line.delivery_picking_orig_id, picking)
        self.assertEqual(self.purchase.delivery_price, 20)
        new_picking = self.purchase.picking_ids - picking
        new_picking.carrier_id = self.carrier_rules
        self._action_picking_validate(new_picking)
        self.assertEqual(new_picking.carrier_price, 10)
        new_delivery_line = (
            self.purchase.order_line.filtered(lambda x: x.is_delivery) - delivery_line
        )
        self.assertEqual(new_delivery_line.delivery_picking_orig_id, new_picking)
        self.assertEqual(self.purchase.delivery_price, 30)

    def test_onchange_picking_carrier_invoice_policy_real(self):
        self.carrier_rules.invoice_policy = "real"
        self.purchase.carrier_id = False
        self.purchase.button_confirm()
        picking = self.purchase.picking_ids
        picking.carrier_id = self.carrier_rules.id
        self._action_picking_validate(picking)
        self.assertEqual(picking.carrier_id, self.carrier_rules)
        self.assertEqual(picking.carrier_price, 10)
        self.assertEqual(self.purchase.carrier_id, self.carrier_rules)
        delivery_line = self.purchase.order_line.filtered(lambda x: x.is_delivery)
        self.assertEqual(delivery_line.delivery_picking_orig_id, picking)
        self.assertEqual(self.purchase.delivery_price, 10)
