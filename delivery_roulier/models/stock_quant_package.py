# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from functools import wraps
import logging
import base64

from openerp import models, api, fields
from openerp.tools.translate import _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import (
        InvalidApiInput,
        CarrierError
    )
except ImportError:
    _logger.debug('Cannot `import roulier`.')


def implemented_by_carrier(func):
    """Decorator: call _carrier_prefixed method instead.

    Usage:
        @implemented_by_carrier
        def _do_something()
        def _laposte_do_something()
        def _gls_do_something()

    At runtime, picking._do_something() will try to call
    the carrier spectific method or fallback to generic _do_something

    """
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        fun_name = func.__name__

        def get_carrier_type(cls, *args, **kwargs):
            if hasattr(cls, 'carrier_type'):
                return cls.carrier_type
            # TODO: est-ce bien utile si on carrier_id ?
            pickings = [
                obj for obj in args
                if getattr(obj, '_name', '') == 'stock.picking']
            if len(pickings) > 0:
                return pickings[0].carrier_type
            if cls[0].carrier_id:
                return cls[0].carrier_id.carrier_type

        carrier_type = get_carrier_type(cls, *args, **kwargs)
        fun = '_%s%s' % (carrier_type, fun_name)
        if not hasattr(cls, fun):
            fun = '_roulier%s' % (fun_name)
            # return func(cls, *args, **kwargs)
        return getattr(cls, fun)(*args, **kwargs)
    return wrapper


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")

    # helper : move it to base ?
    @api.multi
    def get_operations(self):
        """Get operations of the package.

        Usefull for having products and quantities
        """
        self.ensure_one()
        return self.env['stock.pack.operation'].search([
            ('result_package_id', '=', self.id),
            ('product_id', '!=', False),
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
    def _get_customs(self, picking):
        pass

    @implemented_by_carrier
    def _should_include_customs(self, picking):
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
    def _prepare_label(self, label, picking):
        pass

    @implemented_by_carrier
    def _handle_attachments(self, label, response):
        pass

    @implemented_by_carrier
    def _handle_tracking(self, label, response):
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
    # end of API

    # Core functions
    @api.multi
    def _roulier_generate_labels(self, picking):
        # by default, only one pack per call
        for package in self:
            response = package._call_roulier_api(picking)
            package._handle_tracking(picking, response)
            package._handle_attachments(picking, response)

    @api.multi
    def _roulier_get_parcels(self, picking):
        # by default, only one pack per call
        self.ensure_one()
        return [self._get_parcel(picking)]

    @api.multi
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

    @api.multi
    def _call_roulier_api(self, picking):
        """Create a label for a given package_id (self)."""
        # There is low chance you need to override it.
        # Don't forget to implement _a-carrier_before_call
        # and _a-carrier_after_call
        self.write({'carrier_id': picking.carrier_id.id})
        roulier_instance = roulier.get(picking.carrier_type)
        payload = roulier_instance.api()

        sender = picking._get_sender(self)
        receiver = picking._get_receiver(self)

        payload['auth'] = picking._get_auth(self)

        payload['from_address'] = picking._convert_address(sender)
        payload['to_address'] = picking._convert_address(receiver)
        if self._should_include_customs(picking):
            payload['customs'] = self._get_customs(picking)

        payload['service'] = picking._get_service(self)
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
    @api.multi
    def _roulier_get_parcel(self, picking):
        self.ensure_one()
        weight = self.weight
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

    def _roulier_should_include_customs(self, picking):
        """Choose if custom docs should be sent.

        Really dumb implementation.
        You may improve this for your carrier.
        """
        sender = picking._get_sender(self)
        receiver = picking._get_receiver(self)
        return sender.country_id.code != receiver.country_id.code

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
        return _(u'Sent data:\n%s\n\nException raised:\n%s\n' % (
            payload, exception.message))

    def _roulier_invalid_api_input_handling(self, payload, exception):
        """Build exception message for bad input.

        It's happend when your data is not valid, like a missing value
        in the payload.

        You may improve this for your carrier.
        returns:
            string
        """
        return _(u'Bad input: %s\n' % exception.message)

    @api.multi
    def _roulier_get_customs(self, picking):
        """Format customs infos for each product in the package.

        The decision whether to include these infos or not is
        taken in _should_include_customs()

        Returns:
            dict.'articles' : list with qty, weight, hs_code
            int category: gift 1, sample 2, commercial 3, ...
        """
        self.ensure_one()

        articles = []
        for operation in self.get_operations():
            article = {}
            articles.append(article)
            product = operation.product_id
            # stands for harmonized_system
            hs = product.product_tmpl_id.get_hs_code_recursively()

            article['quantity'] = '%.f' % operation.product_qty
            article['weight'] = (
                operation.get_weight() / operation.product_qty)
            article['originCountry'] = product.origin_country_id.code
            article['description'] = hs.description
            article['hs'] = hs.hs_code
            article['value'] = product.list_price  # unit price is expected

        category = picking.customs_category
        return {
            "articles": articles,
            "category": category,
        }

    # There is low chance you need to override the following methods.
    @api.multi
    def _roulier_handle_attachments(self, picking, response):
        labels = []
        parcels = iter(response.get('parcels', []))
        for rec in self:
            parcel_rep = parcels.next()
            main_label = rec._roulier_prepare_label(picking, parcel_rep)
            labels.append(
                self.env['shipping.label'].create(main_label)
            )
        attachments = [
            self.env['ir.attachment'].create(attachment)
            for attachment in
            self[0]._roulier_prepare_attachments(picking, response)
        ]  # do it once for all
        return {
            'labels': labels,
            'attachments': attachments,
        }

    @api.multi
    def _roulier_prepare_label(self, picking, response):
        """Prepare a dict for building a shipping.label.

        The shipping label is what you stick on your packages.
        returns:
            dict
        """
        self.ensure_one()
        label = response.get('label')
        return {
            'res_id': picking.id,
            'res_model': 'stock.picking',
            'package_id': self.id,
            'name': "%s %s" % (self.name, label['name']),
            'datas': base64.b64encode(label['data']),
            'type': 'binary',
            'datas_fname': "%s-%s.%s" % (
                self.name, label['name'], label['type']),
        }

    @api.multi
    def _roulier_prepare_attachments(self, picking, response):
        """Prepare a list of dicts for building ir.attachemens.

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
            'datas': base64.b64encode(attachment['data']),
            'type': 'binary',
            'datas_fname': "%s-%s.%s" % (
                self.name, attachment['name'], attachment['type']),
        } for attachment in attachments]

    @api.multi
    def _roulier_handle_tracking(self, picking, response):
        number = False
        tracking = response.get('tracking')
        if tracking:
            number = tracking.get('number')
        for rec in self:
            rec.parcel_tracking = number
