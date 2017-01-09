# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
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

        if picking.carrier_code == "DPD_Relais":
            request['service']['dropOffLocation'] = \
                self._dpd_dropoff_site(picking)
        return request

    def _dpd_after_call(self, picking, response):
        # import pdb; pdb.set_trace()
        custom_response = {
            'name': response['barcode'],
            'data': response.get('label'),
        }
        return custom_response

    @api.model
    def _dpd_error_handling(self, payload, response):
        payload['auth']['password'] = '****'

        def _getmessage(payload, response):
            message = u'Données transmises:\n' \
                      u'%s\n\nExceptions levées %s' \
                      u'\n' % (payload, response)
            return message

        if 'Input error ' in response:
            # InvalidInputException
            # on met des clés plus explicites vis à vis des objets odoo
            suffix = (
                u"\nSignification des clés dans le contexte Odoo:\n"
                u"- 'to_address' : adresse du destinataire (votre client)\n"
                u"- 'from_address' : adresse de l'expéditeur (vous)")
            message = u'Données transmises:\n%s\n\nExceptions levées %s' \
                      u'\n%s' % (payload, response, suffix)
            return message
        elif 'message' in response:
            message = _getmessage(payload, response)
            return message
        elif response['status'] == 'error':
            message = _getmessage(payload, response)
            return message
        else:
            message = "Error Unknown"
            return message

    @api.multi
    def _dpd_dropoff_site(self, picking):
        return 'P22895'  # TODO implement this

    def _dpd_should_include_customs(self, picking):
        """DPD does not return customs documents"""
        return False
