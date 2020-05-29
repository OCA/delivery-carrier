# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _chronopost_fr_get_auth(self, account, package=None):
        vals = self._roulier_get_auth(account, package=package)
        if account.chronopost_fr_subaccount:
            vals.update({
                'subAccount': account.chronopost_fr_subaccount
            })
        return vals

    def _chronopost__fr_get_shipping_date(self, package=None):
        return datetime.now().strftime(DATE_FORMAT)

    def _chronopost_fr_get_service(self, account, package=None):
        vals = self._roulier_get_service(account, package=package)
        additional_vals = {
            'shippingId': self.name,
            'customerId': self.origin,
            'shippingHour': int(datetime.now().strftime("%H")),
            'service': '0',  # default value, overiden by option
        } 
        vals.update(additional_vals)
        return vals

    def _chronopost_fr_get_from_address(self, package=None):
        vals = self._roulier_get_from_address(package=package)
        # Civility for shipper seems always requirer...
        vals['civility'] = 'E'
        return vals
