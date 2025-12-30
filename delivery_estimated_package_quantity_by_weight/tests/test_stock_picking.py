# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestStockPicking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product_carrier = cls.env["product.product"].create(
            {
                "name": "Product Carrier",
                "sale_ok": False,
                "type": "service",
            }
        )

        cls.partner = cls.env["res.partner"].create(
            {"name": "Unittest partner", "ref": "12344566777878"}
        )

        cls.delivery_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Unittest delivery carrier",
                "maximum_weight_per_package": 37,
                "product_id": cls.product_carrier.id,
            }
        )

        cls.package_type = cls.env["stock.package.type"].create(
            {
                "name": "Pack Type 1",
            }
        )

        cls.warehouse_1 = cls.env["stock.warehouse"].create(
            {
                "name": "Base Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "pick_ship",
                "code": "BWH",
            }
        )

        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0001",
                "default_code": "12341",
                "weight": 25,
            }
        )

        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Product 2",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0002",
                "default_code": "12342",
                "weight": 30,
            }
        )

        cls.product3 = cls.env["product.product"].create(
            {
                "name": "Product 3",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0003",
                "default_code": "12343",
                "weight": 30,
            }
        )

        cls.product4 = cls.env["product.product"].create(
            {
                "name": "Product 4",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0004",
                "default_code": "12344",
                "weight": 0.3,
            }
        )

        cls.product5 = cls.env["product.product"].create(
            {
                "name": "Product 5",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0005",
                "default_code": "12345",
                "weight": 3,
            }
        )

        cls.product6 = cls.env["product.product"].create(
            {
                "name": "Product 6",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0006",
                "default_code": "12346",
                "weight": 8,
            }
        )

        cls.product7 = cls.env["product.product"].create(
            {
                "name": "Product 7",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0007",
                "default_code": "12347",
                "weight": 0.6,
            }
        )

        cls.product8 = cls.env["product.product"].create(
            {
                "name": "Product 8",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0008",
                "default_code": "12348",
                "weight": 2,
            }
        )

        cls.product9 = cls.env["product.product"].create(
            {
                "name": "Product 9",
                "sale_ok": True,
                "type": "consu",
                "is_storable": True,
                "list_price": 10,
                "barcode": "XXX0009",
                "default_code": "12349",
                "weight": 12,
            }
        )

        cls.products = [
            cls.product1,
            cls.product2,
            cls.product3,
            cls.product4,
            cls.product5,
            cls.product6,
            cls.product7,
            cls.product8,
            cls.product9,
        ]

        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.picking_type_out.default_location_src_id = cls.warehouse_1.lot_stock_id.id
        cls.picking_type_out.default_location_dest_id = cls.env.ref(
            "stock.stock_location_customers"
        ).id

        cls.stock_location = cls.warehouse_1.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        cls.so = cls._confirm_sale_order(
            partner=cls.partner, products=cls.products, carrier=cls.delivery_carrier
        )

    @classmethod
    def _confirm_sale_order(cls, partner=None, products=None, qty=10, carrier=None):
        Sale = cls.env["sale.order"]
        lines = [
            Command.create(
                {
                    "name": p.name,
                    "product_id": p.id,
                    "product_uom_qty": qty,
                    "product_uom": p.uom_id.id,
                    "price_unit": 1,
                },
            )
            for p in products
        ]
        so_values = {
            "partner_id": partner.id,
            "warehouse_id": cls.warehouse_1.id,
            "order_line": lines,
        }
        if carrier:
            so_values["carrier_id"] = carrier.id

        so = Sale.create(so_values)
        so.action_confirm()

        # Set carrier and picking type on pickings
        for picking in so.picking_ids:
            picking.carrier_id = carrier
            picking.picking_type_code = "outgoing"

        return so

    def test_all_products(self):
        """
        Data:
            All the products are in the SO, some are heavy, others light
        Test case:
            Check the number of packages in the shipping.
            Each box should not exceed 37 kg
        Expected result:
            34 packages
        """
        ship = self.so.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing")
        ship.carrier_id = self.delivery_carrier
        ship.picking_type_code = "outgoing"
        ship.invalidate_recordset()
        ship.is_number_of_packages_visible = True
        ship._compute_theoretical_number_of_packages()

        self.assertEqual(ship.theoretical_number_of_packages, 34)

    def test_light_products(self):
        """
        Data:
            Only light products are considered here
        Test case:
            Check the number of packages in the shipping.
            Each box should not exceed 37 kg
        Expected result:
            1 package is enough
        """
        products = [
            self.product4,
            self.product5,
            self.product6,
            self.product7,
            self.product8,
            self.product9,
        ]
        so = self._confirm_sale_order(
            partner=self.partner,
            products=products,
            qty=1,
            carrier=self.delivery_carrier,
        )

        ship = so.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing")
        ship.invalidate_recordset()
        ship.is_number_of_packages_visible = True
        ship._compute_theoretical_number_of_packages()

        self.assertEqual(ship.theoretical_number_of_packages, 1)

    def test_one_product(self):
        """
        Data:
            Only one product is considered here
        Test case:
            Check the number of packages in the shipping.
            Each box should not exceed 37 kg
        Expected result:
            1 package is enough
        """
        so = self._confirm_sale_order(
            partner=self.partner,
            products=[self.product4],
            qty=1,
            carrier=self.delivery_carrier,
        )

        ship = so.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing")
        ship.invalidate_recordset()
        ship.is_number_of_packages_visible = True
        ship._compute_theoretical_number_of_packages()

        self.assertEqual(ship.theoretical_number_of_packages, 1)

    def test_heavy_products(self):
        """
        Data:
            Only heavy products are considered here
        Test case:
            Check the number of packages in the shipping.
            Each box should not exceed 30 kg
        Expected result:
            30 packages are needed, one by product
        """
        products = [self.product1, self.product2, self.product3]
        so = self._confirm_sale_order(
            partner=self.partner,
            products=products,
            qty=10,
            carrier=self.delivery_carrier,
        )

        ship = so.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing")
        ship.invalidate_recordset()
        ship.is_number_of_packages_visible = True
        ship._compute_theoretical_number_of_packages()

        self.assertEqual(ship.theoretical_number_of_packages, 30)

    def test_put_in_pack(self):
        """Test putting products in packages and validating picking"""
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.delivery_carrier.id,
                "picking_type_code": "outgoing",
            }
        )

        self.env["stock.move"].create(
            {
                "name": self.product9.name,
                "product_id": self.product9.id,
                "product_uom_qty": 2,
                "product_uom": self.product9.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        picking.action_confirm()
        self.assertTrue(picking.is_number_of_packages_visible)
        self.assertEqual(picking.theoretical_number_of_packages, 1)
        self.assertEqual(picking.number_of_packages_done, 0)
        self.assertFalse(picking.is_number_of_packages_outranged)

        # First put in pack with quantity 1
        picking.move_ids.quantity = 1
        pack_action = picking.action_put_in_pack()
        pack_action_ctx = pack_action["context"]
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({"delivery_package_type_id": self.package_type.id})
        )
        pack_wiz.action_put_in_pack()
        self.assertEqual(picking.number_of_packages_done, 1)
        self.assertFalse(picking.is_number_of_packages_outranged)

        # Second put in pack with quantity 2
        picking.move_ids.quantity = 2
        pack_action = picking.action_put_in_pack()
        pack_action_ctx = pack_action["context"]
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({"delivery_package_type_id": self.package_type.id})
        )
        pack_wiz.action_put_in_pack()
        self.assertEqual(picking.number_of_packages_done, 2)
        self.assertTrue(picking.is_number_of_packages_outranged)

        # Validate picking
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def test_number_of_packages_edge_cases(self):
        """Test edge cases for package number computations"""
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        picking._compute_is_number_of_packages_visible()
        self.assertFalse(picking.is_number_of_packages_visible)

        # No carrier maximum weight
        picking.carrier_id = self.delivery_carrier
        self.delivery_carrier.maximum_weight_per_package = 0
        picking._compute_is_number_of_packages_visible()
        self.assertFalse(picking.is_number_of_packages_visible)

        # No moves
        picking._compute_theoretical_number_of_packages()
        self.assertFalse(picking.theoretical_number_of_packages)

        # No move lines
        picking._compute_number_of_packages_done()
        self.assertFalse(picking.number_of_packages_done)

        # Number of packages not visible
        picking._compute_is_number_of_packages_outranged()
        self.assertFalse(picking.is_number_of_packages_outranged)

    def test_packages_with_no_weight(self):
        """
        Test package computations with products having no weight
        """
        # Create a product with no weight
        product_no_weight = self.env["product.product"].create(
            {
                "name": "No Weight Product",
                "type": "consu",
                "weight": 0.0,
            }
        )

        # Create picking with proper carrier_id reference
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.delivery_carrier.id,  # Pass the ID instead of record
            }
        )

        # Set picking type code after creation
        picking.picking_type_id.code = "outgoing"

        # Add move with the no-weight product
        self.env["stock.move"].create(
            {
                "name": product_no_weight.name,
                "product_id": product_no_weight.id,
                "product_uom_qty": 1,
                "product_uom": product_no_weight.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        picking.action_confirm()
        self.delivery_carrier.maximum_weight_per_package = 37

        # Force recompute all required fields
        picking.invalidate_recordset()
        picking._compute_is_number_of_packages_visible()
        picking._compute_theoretical_number_of_packages()
        picking._compute_number_of_packages_done()
        picking._compute_is_number_of_packages_outranged()

        self.assertTrue(picking.is_number_of_packages_visible)
        self.assertEqual(picking.theoretical_number_of_packages, 1)
        self.assertEqual(picking.number_of_packages_done, 0)
        self.assertFalse(picking.is_number_of_packages_outranged)
