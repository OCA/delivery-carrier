# -*- coding: utf-8 -*-
# Copyright 2012 Guewen Baconnier
# Copyright 2018 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class CarrierFilesDocumentTest(TransactionCase):

    def test_carrier_file_generation(self):
        """ Test carrier file generation """
        carrier_file = self.env.ref(
            'base_delivery_carrier_files.delivery_carrier_file')

        # Save as attachment
        carrier_file.write({'write_mode': 'document'})

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
        domain = [('datas_fname', '=ilike', '%.csv')]
        count_before = self.env['ir.attachment'].search_count(domain)
        picking.do_transfer()
        count_after = self.env['ir.attachment'].search_count(domain)

        # I check shipment details after shipment
        # The carrier file must have been generated.
        self.assertTrue(picking.carrier_file_generated)
        # The carrier file attachment must be there
        self.assertEquals(count_after - count_before, 1)
