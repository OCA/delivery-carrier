# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.exceptions import ValidationError

from odoo.addons.stock.tests.test_packing import TestPackingCommon


class TestDeliveryCarrierPackageMeasureRequire(TestPackingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.normal_carrier = cls.env.ref("delivery.normal_delivery_carrier")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.product_aw = cls.env["product.product"].create(
            {
                "name": "Product AW",
                "type": "product",
                "weight": 2.4,
                "uom_id": cls.uom_kg.id,
                "uom_po_id": cls.uom_kg.id,
            }
        )
        cls.packaging = cls.env["product.packaging"].create(
            {"name": "Test Delivery Packaging"}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_aw, cls.stock_location, 20.0
        )
        cls.pick = cls.env["stock.picking"].create(
            {
                "partner_id": cls.env["res.partner"].create({"name": "A partner"}).id,
                "picking_type_id": cls.warehouse.out_type_id.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "carrier_id": cls.normal_carrier.id,
            }
        )
        cls.env["stock.move.line"].create(
            {
                "product_id": cls.product_aw.id,
                "product_uom_id": cls.uom_kg.id,
                "picking_id": cls.pick.id,
                "qty_done": 5,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )
        cls.pick.action_confirm()

    def test_required_measurement_are_properly_set(self):
        """Check required measurement are fullfilled on validation."""
        pack_action = self.pick.action_put_in_pack()
        pack_action_ctx = pack_action["context"]
        pack_wiz = (
            self.env["choose.delivery.package"].with_context(pack_action_ctx).create({})
        )
        pack_wiz.action_put_in_pack()
        package = self.pick.move_line_ids.mapped("result_package_id")
        package.packaging_id = self.packaging
        # No measurement required
        self.pick._check_required_package_measurement()
        # Check length is required
        self.packaging.package_length_required = True
        with self.assertRaises(ValidationError):
            self.pick.button_validate()
        package.pack_length = 55
        self.pick._check_required_package_measurement()
        # Check width is required
        self.packaging.package_width_required = True
        with self.assertRaises(ValidationError):
            self.pick._check_required_package_measurement()
        package.width = 25
        self.pick._check_required_package_measurement()
        # Check weight is required
        self.packaging.package_weight_required = True
        package.shipping_weight = False
        with self.assertRaises(ValidationError):
            self.pick._check_required_package_measurement()
        package.shipping_weight = 250
        self.pick._check_required_package_measurement()
        # Check height is required
        self.packaging.package_height_required = True
        with self.assertRaises(ValidationError):
            self.pick._check_required_package_measurement()
        package.height = 250
        self.pick._check_required_package_measurement()
        # Missing requirement on validate
        package.width_required = False
        package.width = False
        package.width_required = True
        with self.assertRaises(ValidationError):
            self.pick.button_validate()
