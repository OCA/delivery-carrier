# Copyright 2012 Guewen Baconnier
# Copyright 2018 Sunflower IT (http://sunflowerweb.nl)
# Copyright 2021 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class CarrierFilesDocumentTest(TransactionCase):

    def test_carrier_file_generation(self):
        """ Test carrier file generation """
        carrier_file = self.env.ref(
            'base_delivery_carrier_files.delivery_carrier_file')

        # Save as attachment
        carrier_file.write({'write_mode': 'document'})

        # I set the carrier file configuration on the carrier
        # 'The Poste charges'
        carrier = self.env.ref('delivery.delivery_carrier')
        carrier.carrier_file_id = carrier_file.id

        # I confirm outgoing shipment of Drawer.
        picking = self.env.ref('stock.outgoing_shipment_main_warehouse')
        # in order to generate carrier file we need to assign a valid carrier
        picking.carrier_id = carrier.id

        if not picking.carrier_file_generated:
            # Mark as todo
            picking.action_confirm()
            # I check stock availability.
            picking.action_assign()
            # create the attachment
            # Generate carrier file for the picking
            wiz = self.env['delivery.carrier.file.generate']\
                .with_context(
                active_model='stock.picking',
                active_ids=[picking.id]
            ).create({
                'pickings': [(6, 0, [picking.id])],
                'recreate': True
            })
            wiz.action_generate()
            # I deliver outgoing shipment.
            picking.button_validate()
            # I check shipment details after shipment
            # The carrier file must have been generated.
            self.assertTrue(picking.carrier_file_generated)
