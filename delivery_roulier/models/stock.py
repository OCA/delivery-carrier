# coding: utf-8
#  @author Raphael Reverdy @ Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from functools import wraps
import logging

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # base_delivery_carrier_label API implementataion

    # @api.multi
    # def generate_default_label(self, package_ids=None):
    # useless method

    customs_category = fields.Selection(
        selection=[
            ('gift', _("Gift")),
            ('sample', _("Samples")),
            ('commercial', _("Commercial Goods")),
            ('document', _("Documents")),
            ('other', _("Other")),
            ('return', _("Goods return")),
        ],
        default='commercial',
        help="Type of sending for the customs")
    display_insurance = fields.Boolean(
        compute='_compute_check_options',
        string="Define a condition to display/hide your custom Insurance"
               "field with a decated view")

    @api.multi
    @api.depends('option_ids')
    def _compute_check_options(self):
        insurance_opt = self.env.ref(
            'delivery_roulier.carrier_opt_tmpl_INS', False)
        for rec in self:
            if insurance_opt in [x.tmpl_option_id for x in rec.option_ids]:
                rec.display_insurance = True
            else:
                rec.display_insurance = False
                _logger.info("   >>> in _compute_check_options() %s" %
                             rec.display_insurance)

    @implemented_by_carrier
    def _get_sender(self, package):
        pass

    @implemented_by_carrier
    def _get_receiver(self, package):
        pass

    @implemented_by_carrier
    def _get_shipping_date(self, package):
        pass

    @implemented_by_carrier
    def _map_options(self):
        pass

    @implemented_by_carrier
    def _get_options(self, package):
        pass

    @implemented_by_carrier
    def _get_account(self, package):
        pass

    @implemented_by_carrier
    def _get_auth(self, package):
        pass

    @implemented_by_carrier
    def _get_service(self, package):
        pass

    @implemented_by_carrier
    def _convert_address(self, partner):
        pass

    @api.multi
    def _is_roulier(self):
        self.ensure_one()
        return self.carrier_type in roulier.get_carriers()

    @api.multi
    def generate_labels(self, package_ids=None):
        """See base_delivery_carrier_label/stock.py."""
        # entry point
        self.ensure_one()
        if self._is_roulier():
            return self._roulier_generate_labels()
        _super = super(StockPicking, self)
        return _super.generate_labels(package_ids=package_ids)

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """See base_delivery_carrier_label/stock.py."""
        self.ensure_one()

        if self._is_roulier():
            raise UserError(_("Don't call me directly"))
        _super = super(StockPicking, self)
        return _super.generate_shipping_labels(package_ids=package_ids)

    @api.multi
    def _roulier_generate_labels(self):
        """Create as many labels as package_ids or in self."""
        self.ensure_one()
        packages = self._get_packages_from_picking()
        if not packages:
            # It's not our responsibility to create the packages
            raise UserError(_('No package found for this picking'))
        return packages._generate_labels(self)

    # default implementations
    def _roulier_get_auth(self, package):
        """Login/password of the carrier account.

        Returns:
            a dict with login and password keys
        """
        account = self._get_account(package)
        auth = {
            'login': account.login,
            'password': account.get_password(),
        }
        return auth

    def _roulier_get_account(self, package):
        """Return an 'account'.

        By default, the first account encoutered for this type.
        Depending on your case, you may store it on the picking or
        compute it from your business rules.

        Accounts are resolved at runtime (can be != for dev/prod)
        """
        keychain = self.env['keychain.account']
        if self.env.user.has_group('stock.group_stock_user'):
            retrieve = keychain.suspend_security().retrieve
        else:
            retrieve = keychain.retrieve
        accounts = retrieve(
            [['namespace', '=', 'roulier_%s' % self.carrier_type]])
        return accounts[0]

    def _roulier_get_service(self, package):
        shipping_date = self._get_shipping_date(package)

        service = {
            'product': self.carrier_code,
            'shippingDate': shipping_date,
        }
        return service

    def _roulier_get_sender(self, package):
        """Sender of the picking (for the label).

        Return:
            (res.partner)
        """
        return self.company_id.partner_id

    def _roulier_get_receiver(self, package):
        """The guy who the shippment is for.

        At home or at a distribution point, it's always
        the same receiver address.

        Return:
            (res.partner)
        """
        return self.partner_id

    def _roulier_get_shipping_date(self, package):
        tomorrow = datetime.now() + timedelta(1)
        return tomorrow.strftime('%Y-%m-%d')

    @api.model
    def _roulier_map_options(self):
        """ Customize this mapping with your own carrier as this example:
            return {
                'FCR': 'fcr',
                'COD': 'cod',
                'INS': 'ins',
            }
        """
        return {}

    def _roulier_get_options(self, package):
        mapping_options = self._map_options()
        options = {}
        if self.option_ids:
            for opt in self.option_ids:
                opt_key = str(opt.tmpl_option_id['code'])
                if opt_key in mapping_options:
                    options[mapping_options[opt_key]] = True
                else:
                    options[opt_key] = True
        return options

    @api.model
    def _roulier_convert_address(self, partner):
        """Convert a partner to an address for roulier.

        params:
            partner: a res.partner
        return:
            dict
        """
        address = {}
        extract_fields = [
            'company', 'name', 'zip', 'city', 'phone', 'mobile',
            'email', 'street2']
        for elm in extract_fields:
            if elm in partner:
                # because a value can't be None in odoo's ORM
                # you don't want to mix (bool) False and None
                if partner._fields[elm].type != fields.Boolean.type:
                    if partner[elm]:
                        address[elm] = partner[elm]
                    # else:
                    # it's a None: nothing to do
                else:  # it's a boolean: keep the value
                    address[elm] = partner[elm]
        if not address.get('company', False) and partner.parent_id.is_company:
            address['company'] = partner.parent_id.name
        # Roulier needs street1 not street
        address['street1'] = partner.street
        # Codet ISO 3166-1-alpha-2 (2 letters code)
        address['country'] = partner.country_id.code
        return address
