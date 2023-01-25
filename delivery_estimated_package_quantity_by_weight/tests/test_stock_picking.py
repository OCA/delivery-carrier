# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0001",
                "default_code": "12341",
            }
        )
        cls.product_template1 = cls.product1.product_tmpl_id
        cls.product_template1.weight = 25

        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Product 2",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0002",
                "default_code": "12342",
            }
        )
        cls.product_template2 = cls.product2.product_tmpl_id
        cls.product_template2.weight = 30

        cls.product3 = cls.env["product.product"].create(
            {
                "name": "Product 3",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0003",
                "default_code": "12343",
            }
        )
        cls.product_template3 = cls.product3.product_tmpl_id
        cls.product_template3.weight = 30

        cls.product4 = cls.env["product.product"].create(
            {
                "name": "Product 4",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0004",
                "default_code": "12344",
            }
        )
        cls.product_template4 = cls.product4.product_tmpl_id
        cls.product_template4.weight = 0.3

        cls.product5 = cls.env["product.product"].create(
            {
                "name": "Product 5",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0005",
                "default_code": "12345",
            }
        )
        cls.product_template5 = cls.product5.product_tmpl_id
        cls.product_template5.weight = 3

        cls.product6 = cls.env["product.product"].create(
            {
                "name": "Product 6",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0006",
                "default_code": "12346",
            }
        )
        cls.product_template6 = cls.product6.product_tmpl_id
        cls.product_template6.weight = 8

        cls.product7 = cls.env["product.product"].create(
            {
                "name": "Product 7",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0007",
                "default_code": "12347",
            }
        )
        cls.product_template7 = cls.product7.product_tmpl_id
        cls.product_template7.weight = 0.6

        cls.product8 = cls.env["product.product"].create(
            {
                "name": "Product 8",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0008",
                "default_code": "12348",
            }
        )
        cls.product_template8 = cls.product8.product_tmpl_id
        cls.product_template8.weight = 2

        cls.product9 = cls.env["product.product"].create(
            {
                "name": "Product 9",
                "sale_ok": True,
                "type": "product",
                "list_price": 10,
                "barcode": "XXX0009",
                "default_code": "12349",
            }
        )
        cls.product_template9 = cls.product9.product_tmpl_id
        cls.product_template9.weight = 12

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
        cls.so = cls._confirm_sale_order(
            partner=cls.partner, products=cls.products, carrier=cls.delivery_carrier
        )

        cls.location_model = cls.env["stock.location"]
        cls.stock_location = cls.location_model.create({"name": "stock_loc"})
        cls.customer_location = cls.location_model.create({"name": "customer_loc"})
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    @classmethod
    def _confirm_sale_order(cls, partner=None, products=None, qty=10, carrier=None):
        if partner is None:
            partner = cls.partner
        if products is None:
            products = [cls.product1]
        warehouse = cls.warehouse_1
        Sale = cls.env["sale.order"]
        lines = [
            (
                0,
                0,
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
            "warehouse_id": warehouse.id,
            "order_line": lines,
        }
        if carrier:
            so_values["carrier_id"] = carrier.id

        so = Sale.create(so_values)
        so.action_confirm()
        return so

    def test_all_products(self):
        """
        Data:
            All the products are in the SO, some are heavy, others light
        Test case:
            Check the number of packages in the shipping. Each box should not exceed 37 kg
            We have a lot of products in this shipping:
            10 product1 with weight of 25kg each => 250kg
            10 product2 with weight of 30kg each => 300kg
            10 product3 with weight of 30kg each => 300kg
            10 product4 with weight of 0.3kg each => 3kg
            10 product5 with weight of 3kg each => 30kg
            10 product6 with weight of 8kg each => 80kg
            10 product7 with weight of 0.6kg each => 6kg
            10 product8 with weight of 2kg each => 20kg
            10 product9 with weight of 12kg each => 120kg

            We will have a list of weights:
            [0.3,0.3,0.3,0.3,0.3,0.3,0.3,0.3,0.3,0.3,
            0.6,0.6,0.6,0.6,0.6,0.6,0.6,0.6,0.6,0.6,
            2,2,2,2,2,2,2,2,2,2,
            3,3,3,3,3,3,3,3,3,3,
            8,8,8,8,8,8,8,8,8,8,
            12,12,12,12,12,12,12,12,12,12,
            25,25,25,25,25,25,25,25,25,25,
            30,30,30,30,30,30,30,30,30,30,
            30,30,30,30,30,30,30,30,30,30]


            All the 0.3kg products will go in one pack with one 30 and 6 products of
              0.6kg leading to a pack of 36.6kg => 1 pack
            4 products of 0.6kg will go with another of 30 and 2 of 2 leading to a
              second pack of 36.4kg => 1 pack
            3 products of 2 kg will go with one of 30 leading to 36kg => 1 pack
            3 products of 2 kg will go with one of 30 leading to 36kg => 1 pack
            2 products of 2 kg will go with one of 30 and one of 3 leading to 37kg
              => 1 pack
            2 products of 3 kg will go with one of 30 leading to 36kg => 1 pack
            2 products of 3 kg will go with one of 30 leading to 36kg => 1 pack
            2 products of 3 kg will go with one of 30 leading to 36kg => 1 pack
            2 products of 3 kg will go with one of 30 leading to 36kg => 1 pack
            1 products of 3 kg will go with one of 30 leading to 36kg => 1 pack
            10 packs of 30
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            1 product of 8 and 1 product of 25 leading to 32kg => 1 pack
            3 products of 12 leading to 36 kg => 1 pack
            3 products of 12 leading to 36 kg => 1 pack
            3 products of 12 leading to 36 kg => 1 pack
            1 remaining of 12 => 1 pack

        Expected result:
            34 packages
        """
        ship = self.so.mapped("picking_ids").filtered(
            lambda p: p.picking_type_code == "outgoing"
        )

        ship._compute_theoretical_number_of_packages()
        self.assertEqual(ship.theoretical_number_of_packages, 34)

    def test_light_products(self):
        """
        Data:
            Only light products are considered here
        Test case:
            Check the number of packages in the shipping. Each box should not exceed
            37 kg
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
        lines = [
            (
                0,
                0,
                {
                    "name": p.name,
                    "product_id": p.id,
                    "product_uom_qty": 1,
                    "product_uom": p.uom_id.id,
                    "price_unit": 1,
                },
            )
            for p in products
        ]
        so_values = {
            "partner_id": self.partner.id,
            "warehouse_id": self.warehouse_1.id,
            "carrier_id": self.delivery_carrier.id,
            "order_line": lines,
        }

        new_so = self.env["sale.order"].create(so_values)
        new_so.action_confirm()
        ship = new_so.mapped("picking_ids").filtered(
            lambda p: p.picking_type_code == "outgoing"
        )

        ship._compute_theoretical_number_of_packages()
        self.assertEqual(ship.theoretical_number_of_packages, 1)

    def test_one_product(self):
        """
        Data:
            Only one product is considered here
        Test case:
            Check the number of packages in the shipping. Each box should not exceed
            37 kg
        Expected result:
            1 package is enough
        """

        so_values = {
            "partner_id": self.partner.id,
            "warehouse_id": self.warehouse_1.id,
            "carrier_id": self.delivery_carrier.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": self.product4.name,
                        "product_id": self.product4.id,
                        "product_uom_qty": 1,
                        "product_uom": self.product4.uom_id.id,
                        "price_unit": 1,
                    },
                )
            ],
        }

        new_so = self.env["sale.order"].create(so_values)
        new_so.action_confirm()
        ship = new_so.mapped("picking_ids").filtered(
            lambda p: p.picking_type_code == "outgoing"
        )

        ship._compute_theoretical_number_of_packages()
        self.assertEqual(ship.theoretical_number_of_packages, 1)

    def test_heavy_products(self):
        """
        Data:
            Only heavy products are considered here
        Test case:
            Check the number of packages in the shipping. Each box should not exceed
            37 kg
        Expected result:
            30 packages are needed, one by product
        """
        products = [self.product1, self.product2, self.product3]
        lines = [
            (
                0,
                0,
                {
                    "name": p.name,
                    "product_id": p.id,
                    "product_uom_qty": 10,
                    "product_uom": p.uom_id.id,
                    "price_unit": 1,
                },
            )
            for p in products
        ]
        so_values = {
            "partner_id": self.partner.id,
            "warehouse_id": self.warehouse_1.id,
            "carrier_id": self.delivery_carrier.id,
            "order_line": lines,
        }

        new_so = self.env["sale.order"].create(so_values)
        new_so.action_confirm()
        ship = new_so.mapped("picking_ids").filtered(
            lambda p: p.picking_type_code == "outgoing"
        )

        ship._compute_theoretical_number_of_packages()
        self.assertEqual(ship.theoretical_number_of_packages, 30)

    def test_put_in_pack(self):
        """
        Create a picking for 2 units of product 9 (weight = 12) and carrier max weight
        for package = 37
         - theoretical_number_of_packages = 1 and is_number_of_packages_visible = True
           and number_of_packages_done = 0 and is_number_of_packages_outranged = False
        Make put in pack each time with quantity_done = 1
         - number_of_packages_done = 1 and is_number_of_packages_outranged still False
        Make put in pack each time with quantity_done = 2
         - number_of_packages_done = 2 and is_number_of_packages_outranged = True
        Validate the picking to show the outranged is non blocking
         - picking state is done
        """
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.delivery_carrier.id,
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
        # make a first put in pack with quantity done 1
        picking.move_ids.quantity_done = 1
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
        # make a second put in pack with quantity done 2
        picking.move_ids.quantity_done = 2
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
        # validate the picking
        picking.button_validate()
        self.assertEqual(picking.state, "done")
