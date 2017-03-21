# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import logging
from openerp.exceptions import Warning as UserError
from openerp import models, fields
_logger = logging.getLogger(__name__)

try:
    from cerberus import Validator
except ImportError:
    _logger.debug('Cannot `import Cerberus`.')


DPD_KEYCHAIN_NAMESPACE = 'roulier_dpd'


class AccountProduct(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[(DPD_KEYCHAIN_NAMESPACE, 'Dpd')])

    def _dpd_schema(self):
        return {
            'customerCountry': {
                'type': 'string', 'default': '250',
                'regex': '\\w{3}',
                'required': True,
            },
            'customerId': {
                'type': 'string',
                'regex': '\\w{6}',
                'default': '123456',
                'required': True,
            },
            'agencyId': {
                'type': 'string',
                'regex': '\\w{3}',
                'default': '123',
                'required': True,
            },
            'labelFormat': {
                'type': 'string',
                'allowed': ['ZPL', 'PDF'],
                'default': 'ZPL',
                'required': True,
            },
        }

    def _roulier_dpd_init_data(self):
        return Validator().normalized({}, self._dpd_schema())

    def _roulier_dpd_validate_data(self, data):
        v = Validator()
        ret = v.validate(data, self._dpd_schema())
        if not ret:
            _logger.info('DPD data not valid')
            raise UserError(v.errors)
        return ret
