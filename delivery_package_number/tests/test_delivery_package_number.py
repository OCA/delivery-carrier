# Copyright 2020 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestDeliveryPackageNumber(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.wh1 = cls.env["stock.warehouse"].create(
            {"name": "TEST WH1", "code": "TST1"}
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "location_id": cls.wh1.lot_stock_id.id,
                "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                "picking_type_id": cls.wh1.int_type_id.id,
            }
        )
        cls.move_line_obj = cls.env["stock.move.line"]
        cls.ml1 = cls.move_line_obj.create(
            {
                "product_id": cls.product.id,
                "product_uom_id": cls.product.uom_id.id,
                "qty_done": 5,
                "location_id": cls.wh1.lot_stock_id.id,
                "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                "picking_id": cls.picking.id,
            }
        )
        cls.ml2 = cls.ml1.copy({"qty_done": 0})

    def test_number_of_packages(self):
        # By default it's computed to 0
        self.assertEqual(self.picking.number_of_packages, 0)
        # We can edit the number of packages as there aren't delivery packages
        picking_form = Form(self.picking)
        picking_form.number_of_packages = 3
        picking_form.save()
        self.assertEqual(self.picking.number_of_packages, 3)
        # We add a package and it recalculates
        self.picking.action_put_in_pack()
        self.assertEqual(self.picking.number_of_packages, 1)
        self.ml2.qty_done = 5
        self.picking.action_put_in_pack()
        self.assertEqual(self.picking.number_of_packages, 2)
        # We can later set it manually if we want to
        picking_form.number_of_packages = 3
        picking_form.save()
        self.assertEqual(self.picking.number_of_packages, 3)

    def test_backorder(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
        order = order_form.save()
        order.action_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity_done = 2
        picking.number_of_packages = 2
        action = picking.with_context(
            test_delivery_package_number=True
        ).button_validate()
        backorder_wizard = Form(
            self.env[action["res_model"]].with_context(**action["context"])
        ).save()
        backorder_wizard.process()
        done_picking = order.picking_ids.filtered(lambda x: x.state == "done")
        new_picking = order.picking_ids - done_picking
        self.assertEqual(done_picking.number_of_packages, 2)
        self.assertEqual(new_picking.number_of_packages, 0)
