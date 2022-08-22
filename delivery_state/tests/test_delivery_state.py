# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import float_compare


class TestDeliveryState(TransactionCase):
    def setUp(self):
        super().setUp()
        product_shipping_cost = self.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": product_shipping_cost.id,
                "fixed_price": 99.99,
            }
        )
        self.product = self.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        self.partner = self.env["res.partner"].create({"name": "Mr. Odoo"})
        self.pricelist = self.env["product.pricelist"].create(
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

    def test_delivery_state(self):
        sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1})
                ],
            }
        )
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(float_compare(delivery_price, 99.99, precision_digits=2), 0)
        self.assertEquals(len(delivery_lines), 1)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        self.assertEquals(picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertTrue(picking.date_shipped)
        self.assertFalse(picking.tracking_state_history)
        picking.tracking_state_update()
        picking.date_delivered = fields.Datetime.now()
        with self.assertRaises(NotImplementedError):
            picking.cancel_shipment()
        self.env["delivery.carrier"]._patch_method(
            "fixed_cancel_shipment", lambda *args: True
        )
        picking.cancel_shipment()
        self.assertEquals(picking.delivery_state, "canceled_shipment")
        self.assertFalse(picking.date_shipped)
        self.assertFalse(picking.date_delivered)
