# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#
##############################################################################
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning

from roulier import roulier
from datetime import datetime, timedelta
from functools import wraps

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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # base_delivery_carrier_label API implementataion

    # @api.multi
    # def generate_default_label(self, package_ids=None):
    # useless method

    @api.multi
    def generate_labels(self, package_ids=None):
        """See base_delivery_carrier_label/stock.py."""
        self.ensure_one()

        if self._is_our():
            return self._roulier_generate_labels(
                package_ids=package_ids)
        _super = super(StockPicking, self)
        return _super.generate_labels(package_ids=package_ids)

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """See base_delivery_carrier_label/stock.py."""
        self.ensure_one()

        if self._is_our():
            return self._roulier_generate_shipping_labels(
                package_ids=package_ids)
        _super = super(StockPicking, self)
        return _super.generate_shipping_labels(package_ids=package_ids)

    # end of base_label API implementataion

    # API
    @implemented_by_carrier
    def _before_call(self, package_id, request):
        pass

    @implemented_by_carrier
    def _after_call(self, package_id, response):
        pass

    @implemented_by_carrier
    def _is_our(self):
        """Indicate if the current record is managed by roulier.

        returns:
            True or False
        """
        pass

    @implemented_by_carrier
    def _get_account(self):
        pass

    @implemented_by_carrier
    def _get_sender(self):
        pass

    @implemented_by_carrier
    def _get_receiver(self):
        pass

    @implemented_by_carrier
    def _get_shipping_date(self, package_id):
        pass

    @implemented_by_carrier
    def _get_options(self, package_id):
        pass

    # end of API

    # Core functions
    @api.multi
    def _roulier_generate_labels(self, package_ids=None):
        # call generate_shipping_labels for each package
        # collect answers from generate_shipping_labels
        # persist it
        self.ensure_one()

        labels = self.generate_shipping_labels(package_ids)
        for label in labels:
            data = {
                'name': label['name'],
                'res_id': self.id,
                'res_model': 'stock.picking',
            }
            if label.get('package_id'):
                data['package_id'] = label['package_id']

            if label.get('url'):
                data['url'] = label['url']
                data['type'] = 'url'
            elif label.get('data'):
                data['datas'] = label['data'].encode('base64')
                data['type'] = 'binary'

            self.env['shipping.label'].create(data)
        return True

    @api.multi
    def _roulier_generate_shipping_labels(self, package_ids=None):
        """Create as many labels as package_ids or in self."""
        self.ensure_one()

        packages = []
        if package_ids:
            packages = package_ids
        else:
            packages = self._get_packages_from_picking()

        labels = [
            self._call_roulier_api(package)
            for package in packages
        ]
        return labels

    def _call_roulier_api(self, package_id):
        """Create a label for a given package_id."""
        # There is low chance you need to override it.
        # Don't forget to implement _a-carrier_before_call
        # and _a-carrier_after_call
        self.ensure_one()

        roulier_instance = roulier.get(self.carrier_type)
        payload = roulier_instance.api()

        # code commun à tous
        account = self._get_account()
        shipping_date = self._get_shipping_date(package_id)
        option = self._get_options(package_id)
        weight = package_id.get_weight()

        sender = self._get_sender()
        receiver = self._get_receiver()

        payload['infos']['contractNumber'] = account['login']
        payload['infos']['password'] = account['password']

        payload['from_address'] = self._roulier_convert_address(sender)
        payload['to_address'] = self._roulier_convert_address(receiver)

        payload['service'] = {
            'productCode': self.carrier_code,
            'shippingDate': shipping_date,
        }
        payload['parcel'] = {
            'weight': weight,
        }

        # sorte d'interceptor ici pour que chacun
        # puisse ajouter ses merdes à payload
        payload = self._before_call(package_id, payload)

        # vrai appel a l'api
        ret = roulier_instance.get_label(payload)

        # minimum error handling
        if ret.get('status', '') == 'error':
            raise Warning(_(ret.get('message', 'WebService error')))

        # give result to someonelese
        return self._after_call(package_id, ret)

    # helpers
    @api.multi
    def _roulier_convert_address(self, partner):
        """Convert a partner to an address for roulier.

        params:
            partner: a res.partner
        return:
            dict
        """
        self.ensure_one()
        address = {}
        extract_fields = [
            'name', 'zip', 'city', 'phone', 'mobile',
            'email', 'phone', 'parent_id']
        for elm in extract_fields:
            if elm in partner:
                # because a value can't be None in odoo's ORM
                # you don't want to mix (bool) False and None
                if partner._fields[elm].type != fields.Boolean.type:
                    if partner[elm]:
                        address[elm] = partner[elm]
                    else:
                        # it's a None
                        False
                else:  # it's a boolean
                    address[elm] = partner[elm]

        # get_split_adress from partner_helper module
        res = partner._get_split_address(partner, 3, 38)
        address['street2'], address['street1'], address['street3'] = res

        # parent_id is None if it's a company
        if 'parent_id' in address:
            address['company'] = address['parent_id'].name

        # Codet ISO 3166-1-alpha-2 (2 letters code)
        address['country'] = partner.country_id.code
        return address

    def _roulier_is_our(self):
        """Called only by non-roulier deliver methods."""
        # don't override it
        return False

    # default implementations

    # if you want to implement your carrier behavior, don't override it,
    # but define your own method instead with your carrier prefix.
    # see documentation for more details about it
    def _roulier_get_account(self):
        """Login/password of the carrier account.

        Returns:
            a dict with login and password keys
        """
        return {
            'login': '',
            'password': '',
        }

    def _roulier_get_sender(self):
        """Sender of the picking (for the label).

        Return:
            (res.partner)
        """
        self.ensure_one()
        return self.company_id.partner_id

    def _roulier_get_receiver(self):
        """The guy who the shippment is for.

        At home or at a distribution point, it's always
        the same receiver address.

        Return:
            (res.partner)
        """
        self.ensure_one()
        return self.partner_id

    def _roulier_get_shipping_date(self, package_id):
        tomorrow = datetime.now() + timedelta(1)
        return tomorrow.strftime('%Y-%m-%d')

    def _roulier_get_options(self, package_id):
        return {}

