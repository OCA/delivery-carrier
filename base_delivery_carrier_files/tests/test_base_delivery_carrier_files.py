# Copyright 2012 Guewen Baconnier
# Copyright 2018 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import tempfile

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class CarrierFilesTest(TransactionCase):
    def setUp(self):
        super(CarrierFilesTest, self).setUp()

        self.carrier_file = self.env["delivery.carrier.file"].create(
            {
                "name": "Generic",
                "type": "generic",
                "auto_export": True,
                "group_pickings": False,
                "write_mode": "disk",
                "export_path": tempfile.gettempdir(),
            }
        )

        self.carrier_file_manual = self.env["delivery.carrier.file"].create(
            {
                "name": "Generic",
                "type": "generic",
                "auto_export": False,
                "group_pickings": True,
                "write_mode": "disk",
                "export_path": tempfile.gettempdir(),
            }
        )

        self.carrier = self.env.ref("delivery.delivery_carrier")
        self.carrier.carrier_file_id = self.carrier_file.id

        self.carrier_manual = self.env.ref("delivery.free_delivery_carrier")
        self.carrier_manual.carrier_file_id = self.carrier_file_manual.id

        self.location_refrigerator = self.env["stock.location"].create(
            {
                "name": "Refrigerator",
                "usage": "internal",
            }
        )

        self.location_delivery_counter = self.env["stock.location"].create(
            {
                "name": "Delivery Counter",
                "usage": "internal",
            }
        )

        self.owner = self.env["res.partner"].create(
            {
                "name": "test_delivery_carrier_file",
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Icecream",
                "type": "consu",
                "categ_id": self.env.ref("product.product_category_all").id,
                "uom_id": self.env.ref("uom.product_uom_kgm").id,
                "uom_po_id": self.env.ref("uom.product_uom_kgm").id,
            }
        )

        self.picking_type = self.env.ref("stock.warehouse0").out_type_id

    def test_carrier_file_generation(self):
        """Test carrier file generation"""
        # I confirm outgoing shipment of 130 kgm Ice-cream.
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.location_refrigerator.id,
                "location_dest_id": self.location_delivery_counter.id,
                "partner_id": self.owner.id,
                "picking_type_id": self.picking_type.id,
                "carrier_id": self.carrier.id,
            }
        )

        self.env["stock.move"].create(
            {
                "name": "test_carrier_file",
                "location_id": self.location_refrigerator.id,
                "location_dest_id": self.location_delivery_counter.id,
                "picking_id": picking.id,
                "product_id": self.product.id,
                "product_uom": self.env.ref("uom.product_uom_kgm").id,
                "product_uom_qty": 130.0,
            }
        )

        picking.action_confirm()

        # I check outgoing shipment after stock availablity in refrigerator.
        picking.action_assign()

        # I deliver the outgoing shipment.
        action = picking.button_validate()
        self.env[action["res_model"]].with_context(action["context"]).create(
            {}
        ).process()

        # I check shipment details after shipment
        # The carrier file must have been generated.
        self.assertTrue(picking.carrier_file_generated)

        # I check outgoing shipment copy
        # The carrier_file_generated field must be unchecked.
        new_picking = picking.copy()
        self.assertFalse(new_picking.carrier_file_generated)

    def test_manual_carrier_file_generation(self):
        """Test manual carrier file generation"""
        # I confirm outgoing shipment of 130 kgm Ice-cream.
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.location_refrigerator.id,
                "location_dest_id": self.location_delivery_counter.id,
                "partner_id": self.owner.id,
                "picking_type_id": self.picking_type.id,
                "carrier_id": self.carrier_manual.id,
            }
        )

        self.env["stock.move"].create(
            {
                "name": "test_carrier_file_manual",
                "location_id": self.location_refrigerator.id,
                "location_dest_id": self.location_delivery_counter.id,
                "picking_id": picking.id,
                "product_id": self.product.id,
                "product_uom": self.env.ref("uom.product_uom_kgm").id,
                "product_uom_qty": 130.0,
            }
        )

        # I confirm outgoing shipment of 130 kgm Ice-cream.
        picking.action_confirm()

        # I check outgoing shipment after stock availablity in refrigerator.
        picking.action_assign()

        # I deliver the outgoing shipment.
        action = picking.button_validate()
        self.env[action["res_model"]].with_context(action["context"]).create(
            {}
        ).process()

        # I check shipment details after shipment
        # The carrier file must NOT have been generated.
        self.assertFalse(picking.carrier_file_generated)

        # I generate the carrier files of my shipment from the wizard
        wizard = (
            self.env["delivery.carrier.file.generate"]
            .with_context({"active_ids": picking.ids, "active_model": "stock.picking"})
            .create({})
        )
        wizard.action_generate()

        # I check shipment details after manual generation
        # The carrier file must have been generated.
        self.assertTrue(picking.carrier_file_generated)
