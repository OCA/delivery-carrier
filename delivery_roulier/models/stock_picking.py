#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
import logging

from odoo import models, fields
from odoo.tools.translate import _
from odoo.exceptions import UserError

from ..decorator import implemented_by_carrier

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
except ImportError:
    _logger.debug('Cannot `import roulier`.')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    # base_delivery_carrier_label API implementataion

    # def generate_default_label(self, package_ids=None):
    # useless method

    # API:

    @implemented_by_carrier
    def _get_sender(self, package=None):
        pass

    @implemented_by_carrier
    def _get_receiver(self, package=None):
        pass

    @implemented_by_carrier
    def _get_shipping_date(self, package):
        pass

    @implemented_by_carrier
    def _get_account(self, package=None):
        pass

    @implemented_by_carrier
    def _get_auth(self, package=None):
        pass

    @implemented_by_carrier
    def _get_service(self, package=None):
        pass

    @implemented_by_carrier
    def _convert_address(self, partner):
        pass

    # End of API.

    # Implementations for base_delivery_carrier_label
    def _is_roulier(self):
        self.ensure_one()
        return self.delivery_type in roulier.get_carriers()

    def generate_labels(self):
        """See base_delivery_carrier_label/models/stock_picking.py."""
        # entry point
        self.ensure_one()
        if self._is_roulier():
            return self._roulier_generate_labels()
        return super().generate_labels()

    def generate_shipping_labels(self):
        """See base_delivery_carrier_label/stock.py."""
        self.ensure_one()
        if self._is_roulier():
            raise UserError(_("Don't call me directly"))
        return super().generate_shipping_labels()

    def _roulier_generate_labels(self):
        """Create as many labels as package_ids or in self."""
        self.ensure_one()
        packages = self._get_packages_from_picking()
        # base_delivery_carrier_label module ensure packages is available
        self.number_of_packages = len(packages)
        self.carrier_tracking_ref = True  # display button in view
        return packages._generate_labels(self)

    # Default implementations of _roulier_*()
    def _roulier_get_auth(self, package):
        """Login/password of the carrier account.

        Returns:
            a dict with login and password keys
        """
        account = self._get_account(package)
        auth = {
            'login': account.login,
            'password': account._get_password(),
            'isTest': not self.carrier_id.prod_environment,
        }
        return auth

    def _roulier_get_account(self, package=None):
        """Return an 'account'.

        By default, the first account encoutered for this type.
        Depending on your case, you may store it on the picking or
        compute it from your business rules.

        Accounts are resolved at runtime (can be != for dev/prod)
        """
        self.ensure_one()
        domain = [
            ("name", "=", self.carrier_id.delivery_type),
            "|",
            ("company_id", "=", self.company_id.id),
            ("company_id", "=", False)
        ]
        account = self.env["carrier.account"].search(domain, limit=1)
        if not account:
            raise UserError(
                _("No account available with name '%s' "
                  "for this carrier" % self.carrier_id.delivery_type))
        return account

    def _roulier_get_sender(self, package=None):
        """Sender of the picking (for the label).

        Return:
            (res.partner)
        """
        return self.company_id.partner_id

    def _roulier_get_receiver(self, package=None):
        """The guy whom the shippment is for.

        At home or at a distribution point, it's always
        the same receiver address.

        Return:
            (res.partner)
        """
        return self.partner_id

    def _roulier_get_shipping_date(self, package):
        """Choose a shipping date.

        By default, it's tomorrow."""
        tomorrow = datetime.now() + timedelta(1)
        return tomorrow.strftime('%Y-%m-%d')

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
        # Roulier needs street1 (mandatory) not street
        address['street1'] = partner.street
        # Codet ISO 3166-1-alpha-2 (2 letters code)
        address['country'] = partner.country_id.code

        for tel in ['mobile', 'phone']:
            if address.get(tel):
                address[tel] = address[tel].replace(u'\u00A0', '')

        address['phone'] = address.get('mobile', address.get('phone'))

        return address

    def _roulier_get_service(self, package):
        """Return a basic dict.

        The carrier implementation may add stuff
        like agency or options.

        return:
            dict
        """
        shipping_date = self._get_shipping_date(package)

        service = {
            'product': self.carrier_code,
            'shippingDate': shipping_date,
        }
        return service

    def open_website_url(self):
        """Open tracking page.

        More than 1 tracking number: display a list of packages
        Else open directly the tracking page
        """
        self.ensure_one()
        if not self._is_roulier():
            return super().open_website_url()

        packages = self._get_packages_from_picking()
        if len(packages) == 0:
            raise UserError(_('No packages found for this picking'))
        elif len(packages) == 1:
            return packages.open_website_url()  # shortpath

        # display a list of pickings
        action = self.env.ref('stock.action_package_view').read()[0]
        action['res_id'] = packages.ids
        action['domain'] = "[('id', 'in', [%s])]" % (
            ",".join(map(str, packages.ids))
        )
        action['context'] = "{'picking_id': %s }" % str(self.id)
        return action
