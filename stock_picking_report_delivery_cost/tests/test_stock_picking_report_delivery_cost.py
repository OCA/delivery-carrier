# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common


class TestStockPickingReportDeliveryCost(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test contact"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "consu"}
        )
        cls.carrier_product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "service",
                "list_price": 5,
                "taxes_id": False,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": cls.carrier_product.id,
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create({"name": "Test pricelist"})
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "carrier_id": cls.carrier.id,
                "pricelist_id": cls.pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 2,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": 300.00,
                        },
                    ),
                ],
            }
        )

    def test_carrier_price_for_report_before(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": self.order.id,
                    "default_carrier_id": self.carrier.id,
                }
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        self.order.action_confirm()
        picking = self.order.picking_ids
        self.assertAlmostEqual(picking.carrier_price_for_report, 5)

    def test_carrier_price_for_report_after(self):
        self.order.action_confirm()
        picking = self.order.picking_ids
        self.assertAlmostEqual(picking.carrier_price_for_report, 0)
        move = picking.move_ids_without_package
        move.qty_done = move.product_qty
        picking.action_done()
        self.assertAlmostEqual(picking.carrier_price_for_report, 5)
