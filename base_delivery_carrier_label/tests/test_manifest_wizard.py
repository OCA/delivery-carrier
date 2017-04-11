# -*- coding: utf-8 -*-
# © 2017 Angel Moya (PESOL)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp import fields, exceptions


class ManifestWizardCase(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(ManifestWizardCase, self).setUp(*args, **kwargs)
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')

    def test_wizard(self):
        """Create manifest wizard.
        """
        wizard = self.env['manifest.wizard'].create({
            'carrier_id': self.free_delivery.id,
            'from_date': fields.Date.today()
        })
        self.assertFalse(wizard.carrier_type)
        with self.assertRaises(exceptions.Warning):
            wizard.get_manifest_file()
