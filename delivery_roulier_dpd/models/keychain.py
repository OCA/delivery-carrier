# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields

DPD_KEYCHAIN_NAMESPACE = 'roulier_dpd'


class AccountProduct(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[(DPD_KEYCHAIN_NAMESPACE, 'Dpd')])

    def _roulier_dpd_init_data(self):
        return {
            'customerCountry': '250',
            'customerId': '',
            'agencyId': '',
            'labelFormat': 'ZPL',
            }

    def _roulier_dpd_validate_data(self, data):
        return True
