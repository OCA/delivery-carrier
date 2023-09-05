# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestDeliveryPackageNumber(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
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
        # By default it's computed to 1
        self.assertEqual(self.picking.number_of_packages, 1)
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

    def test_number_of_packages_backorder(self):
        # Creates a delivery from a sales order
        product2_id = self.env.ref("product.product_product_25_product_template")
        sale_order_id = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_12").id,
                "date_order": datetime.now(),
                "pricelist_id": self.env.ref("product.list0").id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": product2_id.id,
                "name": product2_id.name,
                "product_uom_qty": 10,
                "customer_lead": 0.00,
                "price_unit": product2_id.list_price,
                "order_id": sale_order_id.id,
            }
        )
        sale_order_id.action_confirm()

        # Checks that picking has been generated correctly.
        self.assertEqual(len(sale_order_id.picking_ids), 1)
        pick2_id = sale_order_id.picking_ids[0]
        self.assertEqual(len(pick2_id.move_ids_without_package), 1)
        self.assertEqual(pick2_id.move_ids_without_package[0].product_uom_qty, 10.00)
        self.assertEqual(
            pick2_id.move_ids_without_package[0].forecast_availability, 10.00
        )
        self.assertEqual(pick2_id.move_ids_without_package[0].quantity_done, 0.00)

        # Modify the quantity done and the number of packages
        pick2_id.move_ids_without_package[0].quantity_done = 2
        pick2_id.number_of_packages = 2

        # Checks the number of packages
        self.assertEqual(pick2_id.number_of_packages, 2)

        # Create the backorder
        backorder_wizard_dict = pick2_id.button_validate()
        backorder_wizard = Form(
            self.env[backorder_wizard_dict["res_model"]].with_context(
                **backorder_wizard_dict["context"]
            )
        ).save()
        backorder_wizard.process()

        # Checks that the sale order has two deliveries
        self.assertEqual(len(sale_order_id.picking_ids), 2)

        # Checks that the new delivery has 1 package by default:
        self.assertEqual(sale_order_id.picking_ids[1].number_of_packages, 1)

        # Checks the status and number of packages in the delivery that has
        # been validated
        self.assertEqual(pick2_id.state, "done")
        self.assertEqual(pick2_id.number_of_packages, 2)
