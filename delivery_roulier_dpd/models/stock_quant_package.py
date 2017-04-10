# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models
import logging

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _dpd_before_call(self, picking, request):
        account = picking._get_account(self)
        service = account.get_data()
        request['service']['customerCountry'] = service['customerCountry']
        request['service']['customerId'] = service['customerId']
        request['service']['agencyId'] = service['agencyId']
        request['service']['labelFormat'] = service['labelFormat']
        request['service']['product'] = picking.carrier_code
        request['service']['reference1'] = (
            picking.sale_id.name or picking.origin)

        if picking.carrier_code == "DPD_Relais":
            request['service']['dropOffLocation'] = \
                self._dpd_dropoff_site(picking)
            request['service']['notifications'] = 'No'
        return request

    @api.multi
    def _dpd_dropoff_site(self, picking):
        return ''  # like P22895 TODO implement this

    def _dpd_should_include_customs(self, picking):
        """DPD does not return customs documents"""
        return False

    def _dpd_carrier_error_handling(self, payload, exception):
        if self._uid > 1:
            # rm pwd from dict and xml
            payload['auth']['password'] = '****'
        return self._roulier_carrier_error_handling(payload, exception)

    def _dpd_get_tracking_link(self):
        return (
            "http://www.dpd.fr/home/shipping/searchdest.php?"
            "exa=%s" % self.parcel_tracking)
