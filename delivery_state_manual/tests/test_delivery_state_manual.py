# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class SomethingCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_shipping_cost = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": product_shipping_cost.id,
                "fixed_price": 99.99,
                "delivery_state_manual": True,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.partner_shipping = cls.env["res.partner"].create(
            {"name": "Mr. Odoo (shipping)", "email": "test@test.com"}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "partner_shipping_id": cls.partner_shipping.id,
                "pricelist_id": cls.pricelist.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def test_delivery_state_manual(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                **{"default_order_id": self.sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(len(picking.move_ids), 1)
        self.assertEqual(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.move_ids.quantity_done = 1
        picking._action_done()
        self.assertFalse(picking.delivery_state)
        self.assertFalse(picking.date_shipped)
        self.assertFalse(picking.date_delivered)
        picking_form = Form(picking)
        picking_form.delivery_state = "shipping_recorded_in_carrier"
        self.assertTrue(picking_form.date_shipped)
        picking_form.delivery_state = "customer_delivered"
        self.assertTrue(picking_form.date_delivered)
