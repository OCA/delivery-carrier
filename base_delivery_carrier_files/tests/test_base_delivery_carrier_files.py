# -*- coding: utf-8 -*-
# Copyright 2012 Guewen Baconnier
# Copyright 2018 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import tempfile

from openerp.tests.common import TransactionCase


class CarrierFilesTest(TransactionCase):

    def test_carrier_file_generation(self):
        """ Test carrier file generation """
        # I configure the carrier file configuration
        # to write to the root document directory.
        carrier_file = self.env.ref(
            'base_delivery_carrier_files.delivery_carrier_file')
        carrier_file.write({
            'export_path': tempfile.gettempdir(),
            'write_mode': 'disk'
        })

        # I set the carrier file configuration on the carrier
        # 'Free delivery charges'
        carrier = self.env.ref('delivery.delivery_carrier')
        carrier.carrier_file_id = carrier_file.id

        # I confirm outgoing shipment of 130 kgm Ice-cream.
        picking = self.env.ref(
            'base_delivery_carrier_files.outgoing_shipment_carrier_file')
        picking.action_confirm()

        # I check outgoing shipment after stock availablity in refrigerator.
        picking.force_assign()

        # I deliver outgoing shipment.
        wizard = self.env['stock.transfer_details'].with_context({
            'active_model': 'stock.picking',
            'active_id': picking.id,
            'active_ids': picking.ids
        }).create({
            'picking_id': picking.id
        })
        wizard.do_detailed_transfer()

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
        carrier_file = self.env.ref(
            'base_delivery_carrier_files.delivery_carrier_file')
        carrier_file.write({
            'export_path': tempfile.gettempdir(),
            'write_mode': 'disk'
        })

        # I set the carrier file configuration on the carrier
        # 'Free delivery charges'
        carrier = self.env.ref('delivery.delivery_carrier')
        carrier.carrier_file_id = carrier_file.id

        # I confirm outgoing shipment of 130 kgm Ice-cream.
        picking = self.env.ref(
            'base_delivery_carrier_files'
            '.outgoing_shipment_carrier_file_manual')
        picking.action_confirm()

        # I check outgoing shipment after stock availablity in refrigerator.
        picking.force_assign()

        # I deliver outgoing shipment.
        wizard = self.env['stock.transfer_details'].with_context({
            'active_model': 'stock.picking',
            'active_id': picking.id,
            'active_ids': picking.ids
        }).create({
            'picking_id': picking.id
        })
        wizard.do_detailed_transfer()

        # I check shipment details after shipment
        # The carrier file must NOT have been generated.
        self.assertFalse(picking.carrier_file_generated)

        # I generate the carrier files of my shipment from the wizard
        wizard = self.env['delivery.carrier.file.generate'].with_context({
            'active_ids': picking.ids,
            'active_model': 'stock.picking'
        }).create({})
        wizard.action_generate()

        # I check shipment details after manual generation
        # The carrier file must have been generated.
        self.assertTrue(picking.carrier_file_generated)
