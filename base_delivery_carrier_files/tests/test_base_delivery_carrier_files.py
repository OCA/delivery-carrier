# Copyright 2012 Guewen Baconnier
# Copyright 2018 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import tempfile

from odoo.tests import common


class CarrierFilesTest(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.carrier_file = self.env["delivery.carrier.file"].create(
            {
                "name": "Generic",
                "type": "generic",
                "auto_export": True,
                "group_pickings": False,
                "write_mode": "disk",
                "export_path": "/tmp",
            }
        )
        self.carrier_file_manual = self.env["delivery.carrier.file"].create(
            {
                "name": "Generic",
                "type": "generic",
                "auto_export": False,
                "group_pickings": True,
                "write_mode": "disk",
                "export_path": "/tmp",
            }
        )
        self.carrier = self.env.ref("delivery.delivery_carrier")
        self.carrier.carrier_file_id = self.carrier_file.id
        self.carrier_manual = self.env.ref("delivery.free_delivery_carrier")
        self.carrier_manual.carrier_file_id = self.carrier_file_manual.id
        self.location_refrigerator = self.env["stock.location"].create(
            {"name": "Refrigerator", "usage": "internal"}
        )
        self.location_delivery_counter = self.env["stock.location"].create(
            {"name": "Delivery Counter", "usage": "internal"}
        )
        self.owner = self.env["res.partner"].create(
            {"name": "test_delivery_carrier_file"}
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
        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Outgoing Ice Cream",
                "code": "outgoing",
                "sequence_id": self.env.ref("stock.sequence_mrp_op").id,
                "sequence_code": "OIC",
            }
        )

    def _create_picking(self, carrier_id, move_name):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.location_refrigerator.id,
                "location_dest_id": self.location_delivery_counter.id,
                "partner_id": self.owner.id,
                "picking_type_id": self.picking_type.id,
                "carrier_id": carrier_id.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": move_name,
                "location_id": self.location_refrigerator.id,
                "location_dest_id": self.location_delivery_counter.id,
                "picking_id": picking.id,
                "product_id": self.product.id,
                "product_uom": self.env.ref("uom.product_uom_kgm").id,
                "product_uom_qty": 130.0,
            }
        )
        return picking

    def test_carrier_file_generation(self):
        """ Test carrier file generation """
        # I configure the carrier file configuration
        # to write to the root document directory.
        self.carrier_file.write(
            {"export_path": tempfile.gettempdir(), "write_mode": "disk"}
        )
        # I confirm outgoing shipment of 130 kgm Ice-cream.
        picking = self._create_picking(self.carrier, "test_carrier_file")
        picking.action_confirm()
        # I check outgoing shipment after stock availablity in refrigerator.
        picking.action_assign()
        # I deliver outgoing shipment.
        picking.action_done()
        # I check shipment details after shipment
        # The carrier file must have been generated.
        self.assertTrue(picking.carrier_file_generated)
        # I check outgoing shipment copy
        # The carrier_file_generated field must be unchecked.
        new_picking = picking.copy()
        self.assertFalse(new_picking.carrier_file_generated)

    def test_manual_carrier_file_generation(self):
        """ Test manual carrier file generation """
        # I configure the carrier file configuration
        # to write to the root document directory.
        self.carrier_file_manual.write(
            {"export_path": tempfile.gettempdir(), "write_mode": "disk"}
        )
        # I confirm outgoing shipment of 130 kgm Ice-cream.
        picking = self._create_picking(self.carrier_manual, "test_carrier_file_manual")
        picking.action_confirm()
        # I check outgoing shipment after stock availablity in refrigerator.
        picking.action_assign()
        # I deliver outgoing shipment.
        picking.action_done()
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
