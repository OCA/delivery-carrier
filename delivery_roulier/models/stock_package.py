# coding: utf-8
#  @author Raphael Reverdy @ Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from functools import wraps
import logging

from openerp import models, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import InvalidApiInput
except ImportError:
    _logger.debug('Cannot `import roulier`.')

# if you want to integrate a new carrier with Roulier Library
# start from roulier_template.py and read the doc of
# implemented_by_carrier decorator


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
        fun = '_%s%s' % (cls.carrier_type, fun_name)
        if not hasattr(cls, fun):
            fun = '_roulier%s' % (fun_name)
            # return func(cls, *args, **kwargs)
        return getattr(cls, fun)(*args, **kwargs)
    return wrapper


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

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
    def _get_cash_on_delivery(self, picking):
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
    def _error_handling(self, payload, response):
        pass

    @implemented_by_carrier
    def _prepare_label(self, label, picking):
        pass

    # end of API

    # Core functions

    @api.multi
    def _generate_labels(self, picking):
        ret = []
        for package in self:
            labels = package._call_roulier_api(picking)
            if isinstance(labels, dict):
                labels = [labels]
            for label in labels:
                data = package._prepare_label(picking, label)
                ret.append(self.env['shipping.label'].create(data))
        return ret

    def _call_roulier_api(self, picking):
        """Create a label for a given package_id (self)."""
        # There is low chance you need to override it.
        # Don't forget to implement _a-carrier_before_call
        # and _a-carrier_after_call
        self.ensure_one()

        self.carrier_type = picking.carrier_type  # on memory value !
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
        payload['parcel'] = self._get_parcel(picking)

        # hook to override request / payload
        payload = self._before_call(picking, payload)
        try:
            # api call
            ret = roulier_instance.get_label(payload)
        except InvalidApiInput as e:
            raise UserError(self._error_handling(payload, e.message))
        except Exception as e:
            raise UserError(e.message)

        # minimum error handling
        if ret.get('status', '') == 'error':
            raise UserError(self._error_handling(payload, ret))
        # give result to someone else
        return self._after_call(picking, ret)

    # default implementations

    @api.model
    def _roulier_prepare_label(self, picking, label):
        data = {
            'name': label['name'],
            'res_id': picking.id,
            'res_model': 'stock.picking',
            'package_id': self.id,
        }
        if label.get('data'):
            data['datas'] = label['data'].encode('base64')
            data['type'] = 'binary'
        return data

    def _roulier_get_parcel(self, picking):
        weight = self.weight
        parcel = {
            'weight': weight,
        }
        return parcel

    def _roulier_get_cash_on_delivery(self, picking):
        """ called by 'cod' option
        """
        # TODO improve to take account Sale if picking created from sale
        amount = 0
        for oper in self.get_operations():
            amount += oper.product_id.list_price * oper.product_qty
        return amount

    def _roulier_get_customs(self, picking):
        """Format customs infos for each product in the package.

        The decision whether to include these infos or not is
        taken in _should_include_customs()

        Returns:
            dict.'articles' : list with qty, weight, hs_code
            int category: gift 1, sample 2, commercial 3, ...
        """
        try:
            self.env['product.template'].get_hs_code_recursively
        except AttributeError:
            raise UserError(_("Missing module 'intrastat' for customs"))

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

    def _roulier_should_include_customs(self, picking):
        sender = picking._get_sender(self)
        receiver = picking._get_receiver(self)
        return sender.country_id.code != receiver.country_id.code

    @api.model
    def _roulier_error_handling(self, payload, response):
        return _(u'Sent data:\n%s\n\nException raised:\n%s\n' % (
            payload, response))
