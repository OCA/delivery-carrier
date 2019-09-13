#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import base64

from odoo import models, api, fields, _
from odoo.exceptions import UserError

from ..decorator import implemented_by_carrier

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import (
        InvalidApiInput,
        CarrierError
    )
except ImportError:
    _logger.debug('Cannot `import roulier`.')


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")

    # helper : move it to base ?
    def get_operations(self):
        """Get operations of the package.

        Usefull for having products and quantities
        """
        self.ensure_one()
        return self.env['stock.move.line'].search([
            ('product_id', '!=', False),
            '|',
            ('package_id', '=', self.id),
            ('result_package_id', '=', self.id),
        ])

    # API
    # Each method in this class have at least picking arg to directly
    # deal with stock.picking if required by your carrier use case
    @implemented_by_carrier
    def _before_call(self, picking, payload):
        pass

    @implemented_by_carrier
    def _after_call(self, picking, response):
        pass

    @implemented_by_carrier
    def _get_parcel(self, picking):
        pass

    @implemented_by_carrier
    def _carrier_error_handling(self, payload, response):
        pass

    @implemented_by_carrier
    def _invalid_api_input_handling(self, payload, response):
        pass

    @implemented_by_carrier
    def _prepare_attachments(self, picking, response):
        pass

    @implemented_by_carrier
    def _handle_attachments(self, label, response):
        pass

    @implemented_by_carrier
    def _get_tracking_link(self):
        pass

    @implemented_by_carrier
    def _generate_labels(self, picking):
        pass

    @implemented_by_carrier
    def _get_parcels(self, picking):
        pass

    @implemented_by_carrier
    def _parse_response(self, picking, response):
        pass
    # end of API

    # Core functions
    def _roulier_generate_labels(self, picking):
        result = []
        # by default, only one pack per call
        # for now roulier manage one pack at a time by default
        for package in self:
            response = package._call_roulier_api(picking)
            package._handle_attachments(picking, response)
            result.append(self._parse_response(picking, response))
        return result

    def _roulier_parse_response(self, picking, response):
        parcels = response.get('parcels')
        parcel = parcels and parcels[0]
        tracking_number = parcel.get('tracking', {}).get('number')
        # expected format by base_delivery_carrier_label module
        label = parcel.get('label')
        return {
            'tracking_number': tracking_number,
            'package_id': len(self) == 1 and self.id or False,
            'name': (parcel.get('reference') or tracking_number or 
                     label.get('name')),
            'file': label.get('data'),
            'filename': label.get('name'),
            'file_type': label.get('type')
        }

    def _roulier_get_parcels(self, picking):
        # by default, only one pack per call
        self.ensure_one()
        return [self._get_parcel(picking)]

    def open_website_url(self):
        """Open website for parcel tracking.

        Each carrier should implement _get_tracking_link
        There is low chance you need to override this method.
        returns:
            action
        """
        self.ensure_one()
        url = self._get_tracking_link()
        client_action = {
            'type': 'ir.actions.act_url',
            'name': "Shipment Tracking Page",
            'target': 'new',
            'url': url,
        }
        return client_action

    def _call_roulier_api(self, picking):
        """Create a label for a given package_id (self)."""
        # There is low chance you need to override it.
        # Don't forget to implement _a-carrier_before_call
        # and _a-carrier_after_call
        account = picking._get_account(self)
        self.write({'carrier_id': picking.carrier_id.id})
        roulier_instance = roulier.get(picking.delivery_type)
        payload = roulier_instance.api()

        payload['auth'] = picking._get_auth(account, package=self)

        payload['from_address'] = picking._get_from_address(package=self)
        payload['to_address'] = picking._get_to_address(package=self)

        payload['service'] = picking._get_service(account, package=self)
        payload['parcels'] = self._get_parcels(picking)

        # hook to override request / payload
        payload = self._before_call(picking, payload)
        try:
            # api call
            ret = roulier_instance.get_label(payload)
        except InvalidApiInput as e:
            raise UserError(self._invalid_api_input_handling(payload, e))
        except CarrierError as e:
            raise UserError(self._carrier_error_handling(payload, e))

        # give result to someone else
        return self._after_call(picking, ret)

    # default implementations
    def _roulier_get_parcel(self, picking):
        self.ensure_one()
        weight = self.shipping_weight or self.weight
        parcel = {
            'weight': weight,
            'reference': self.name
        }
        return parcel

    def _roulier_before_call(self, picking, payload):
        """Add stuff to payload just before api call.

        Put here what you can't put in other methods
        (like _get_parcel, _get_service...)

        It's totally ok to do nothing here.

        returns:
            dict
        """
        return payload

    def _roulier_after_call(self, picking, response):
        """Do stuff just after api call.

        It's totally ok to do nothing here.
        """
        return response

    def _roulier_get_tracking_link(self):
        """Build a tracking url.

        You have to implement it for your carrier.
        It's like :
            'https://the-carrier.com/?track=%s' % self.parcel_tracking
        returns:
            string (url)
        """
        _logger.warning("not implemented")
        pass

    def _roulier_carrier_error_handling(self, payload, exception):
        """Build exception message for carrier error.

        It's happen when the carrier WS returns something unexpected.
        You may improve this for your carrier.
        returns:
            string
        """
        try:
            _logger.debug(exception.response.text)
            _logger.debug(exception.response.request.body)
        except AttributeError:
            _logger.debug('No request available')
        carrier = dict(self.env['delivery.carrier']._fields[
            'delivery_type'].selection).get(self.carrier_id.delivery_type)
        return _(
            "Roulier library Exception for '%s' carrier:\n"
            "\n%s\n\nSent data:\n%s" % (carrier, str(exception), payload))

    def _roulier_invalid_api_input_handling(self, payload, exception):
        """Build exception message for bad input.

        It's happend when your data is not valid, like a missing value
        in the payload.

        You may improve this for your carrier.
        returns:
            string
        """
        return _('Bad input: %s\n' % exception.message)

    # There is low chance you need to override the following methods.
    def _roulier_handle_attachments(self, picking, response):
        attachments = [
            self.env['ir.attachment'].create(attachment)
            for attachment in
            self[0]._roulier_prepare_attachments(picking, response)
        ]  # do it once for all
        return attachments

    @api.multi
    def _roulier_prepare_attachments(self, picking, response):
        """Prepare a list of dicts for building ir.attachments.
        Attachements are annexes like customs declarations, summary
        etc.
        returns:
            list
        """
        self.ensure_one()
        attachments = response.get('annexes')
        return [{
            'res_id': picking.id,
            'res_model': 'stock.picking',
            'name': "%s %s" % (self.name, attachment['name']),
            'datas': attachment['data'],
            'type': 'binary',
            'datas_fname': "%s-%s.%s" % (
                self.name, attachment['name'], attachment['type']),
        } for attachment in attachments]
