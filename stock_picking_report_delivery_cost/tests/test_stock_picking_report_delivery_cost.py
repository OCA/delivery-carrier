# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestStockPickingReportDeliveryCost(BaseCommon):
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
                    Command.create(
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
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )

    def test_carrier_price_for_report_before(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.order.id,
                default_carrier_id=self.carrier.id,
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        self.order.action_confirm()
        picking = self.order.picking_ids
        self.assertAlmostEqual(picking.carrier_price_for_report, 5)
        # report without errors
        res = self.env["ir.actions.report"]._render(
            "stock.report_deliveryslip", picking.ids
        )
        self.assertRegex(str(res[0]), picking.name)

    def test_carrier_price_for_report_after(self):
        self.order.action_confirm()
        picking = self.order.picking_ids
        self.assertAlmostEqual(picking.carrier_price_for_report, 0)
        move = picking.move_ids_without_package
        move.quantity = move.product_qty
        picking.button_validate()
        self.assertAlmostEqual(picking.carrier_price_for_report, 5)

    def test_picking_manual(self):
        picking_form = Form(
            self.env["stock.picking"].with_context(
                default_picking_type_id=self.warehouse.out_type_id.id,
            )
        )
        picking_form.partner_id = self.partner
        picking_form.carrier_id = self.carrier
        with picking_form.move_ids_without_package.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 1
        picking = picking_form.save()
        picking.carrier_price = 5
        # report without errors
        res = self.env["ir.actions.report"]._render(
            "stock.report_deliveryslip", picking.ids
        )
        self.assertRegex(str(res[0]), picking.name)
