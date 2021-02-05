# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import Form, common


class TestDeliveryPurchase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestDeliveryPurchase, cls).setUpClass()
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

    def test_onchange_partner_id(self):
        self.assertEqual(self.purchase.carrier_id, self.carrier_fixed)

    def test_delivery_purchase(self):
        self.purchase.get_delivery_cost()
        self.assertEqual(self.purchase.delivery_price, 20)
        self.purchase.carrier_id = self.carrier_rules.id
        self.purchase.get_delivery_cost()
        self.assertEqual(self.purchase.delivery_price, 10)
        self.purchase_line.product_id.weight = 8
        self.purchase.get_delivery_cost()
        self.assertEqual(self.purchase.delivery_price, 30)

    def test_picking_carrier(self):
        self.purchase.button_confirm()
        self.assertEqual(
            self.purchase.picking_ids[0].carrier_id, self.carrier_fixed,
        )

    def test_onchange_picking_carrier(self):
        self.purchase.button_confirm()
        picking = self.purchase.picking_ids
        picking.carrier_id = self.carrier_rules.id
        wizard_id = picking.button_validate()["res_id"]
        self.env["stock.immediate.transfer"].browse(wizard_id).process()
        self.assertEqual(picking.carrier_price, 10)
