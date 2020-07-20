# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase
from odoo.tests import Form


class TestDeliveryPackageNumber(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({
            "name": "Test product",
            "type": "product",
        })
        cls.wh1 = cls.env['stock.warehouse'].create({
            'name': 'TEST WH1',
            'code': 'TST1',
        })
        cls.picking = cls.env["stock.picking"].create({
            'location_id': cls.wh1.lot_stock_id.id,
            'location_dest_id': cls.wh1.wh_output_stock_loc_id.id,
            'picking_type_id': cls.wh1.int_type_id.id,
        })
        cls.move_line_obj = cls.env['stock.move.line']
        cls.ml1 = cls.move_line_obj.create({
            'product_id': cls.product.id,
            'product_uom_id': cls.product.uom_id.id,
            'qty_done': 5,
            'location_id': cls.wh1.lot_stock_id.id,
            'location_dest_id': cls.wh1.wh_output_stock_loc_id.id,
            'picking_id': cls.picking.id,
        })
        cls.ml2 = cls.ml1.copy({
            'qty_done': 0,
        })

    def test_number_of_packages(self):
        # By default it's computed to 1
        self.assertEqual(self.picking.number_of_packages, 1)
        # We can edit the number of packages as there aren't delivery packages
        picking_form = Form(self.picking)
        picking_form.number_of_packages = 3
        picking_form.save()
        self.assertEqual(self.picking.number_of_packages, 3)
        # Now we put in pack some quantities and the number of packages is set
        # as the number of packs is added to the number already set
        self.picking.put_in_pack()
        self.assertEqual(self.picking.number_of_packages, 4)
        self.ml2.qty_done = 5
        self.picking.put_in_pack()
        self.assertEqual(self.picking.number_of_packages, 5)
        # We can later set it manually if we want to
        picking_form.number_of_packages = 2
        picking_form.save()
        self.assertEqual(self.picking.number_of_packages, 2)
