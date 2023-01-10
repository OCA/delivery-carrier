# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.stock.tests.test_packing import TestPackingCommon


class TestStockQuantPackageDelivery(TestPackingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.product_test = cls.env["product.product"].create(
            {
                "name": "Product TEST",
                "type": "product",
                "weight": 0.1,
                "uom_id": cls.uom_kg.id,
                "uom_po_id": cls.uom_kg.id,
            }
        )
        test_carrier_product = cls.env["product.product"].create(
            {
                "name": "Test carrier product",
                "type": "service",
            }
        )
        cls.test_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": test_carrier_product.id,
            }
        )
        cls.package_type = cls.env["stock.package.type"].create(
            {
                "name": "package type",
                "number_of_parcels": 7,
            }
        )

    def test_put_in_pack_choose_carrier_wizard(self):
        """
        Trigger the 'choose.delivery.package' wizard and choose a package type with
        a number of parcels > 0.
            - check the related has the right value in the wizard
            - check the related has the right value in the created package
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product_test, self.stock_location, 20.0
        )
        picking_ship = self.env["stock.picking"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "A partner"}).id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.test_carrier.id,
            }
        )
        picking_ship.action_confirm()
        # create a move line for the picking
        self.env["stock.move.line"].create(
            {
                "product_id": self.product_test.id,
                "product_uom_id": self.uom_kg.id,
                "picking_id": picking_ship.id,
                "qty_done": 5,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        pack_action = picking_ship.action_put_in_pack()
        pack_action_ctx = pack_action["context"]
        pack_action_model = pack_action["res_model"]
        # We make sure the correct action was returned
        self.assertEqual(pack_action_model, "choose.delivery.package")
        # check there is no package yet for the picking
        self.assertEqual(len(picking_ship.package_ids), 0)
        # We instanciate the wizard with the context of the action
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({})
        )
        # set the package type
        pack_wiz.delivery_package_type_id = self.package_type
        # check the related number_of_parcels is ok
        self.assertEqual(
            pack_wiz.number_of_parcels, self.package_type.number_of_parcels
        )
        pack_wiz.action_put_in_pack()
        # check that one package has been created with the same number of packages
        self.assertEqual(len(picking_ship.package_ids), 1)
        package1 = picking_ship.package_ids[0]
        # check the related number_of_parcels is ok in the package
        self.assertEqual(
            package1.number_of_parcels, self.package_type.number_of_parcels
        )
