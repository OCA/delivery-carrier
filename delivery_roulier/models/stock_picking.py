#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

from ..decorator import implemented_by_carrier


class StockPicking(models.Model):
    _inherit = "stock.picking"

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
    def _get_auth(self, account, package=None):
        pass

    @implemented_by_carrier
    def _get_service(self, account, package=None):
        pass

    @implemented_by_carrier
    def _convert_address(self, partner):
        pass

    @implemented_by_carrier
    def _get_label_format(self, account):
        pass

    @implemented_by_carrier
    def _get_from_address(self):
        pass

    @implemented_by_carrier
    def _get_to_address(self):
        pass

    @implemented_by_carrier
    def _cancel_shipment(self):
        pass

    # End of API.

    # Implementations for base_delivery_carrier_label
    def _is_roulier(self):
        self.ensure_one()
        return self.carrier_id._is_roulier()

    def _roulier_generate_labels(self):
        """
        Return format expected by send_shipping : a list of dict (one dict per
        picking).
        {
            'exact_price': 0.0,
            'tracking_number': "concatenated numbers",
            'labels': list of dict of labels, managed by base_delivery_carrier_label
        }
        """
        label_info = []
        for picking in self:
            label_info.append(picking.package_ids._generate_labels(picking))
        return label_info

    # Default implementations of _roulier_*()
    def _roulier_get_auth(self, account, package=None):
        """Login/password of the carrier account.

        Returns:
            a dict with login and password keys
        """
        auth = {
            "login": account.account,
            "password": account.password,
            "isTest": not self.carrier_id.prod_environment,
        }
        return auth

    def _roulier_cancel_shipment(self):
        self.write({"carrier_tracking_ref": False})
        labels = self.env["shipping.label"].search(
            [("res_id", "in", self.ids), ("res_model", "=", "stock.picking")]
        )
        labels.mapped("attachment_id").unlink()

    def _roulier_get_account(self, package=None):
        """Return an 'account'.

        By default, the first account encoutered for this type.
        Depending on your case, you may store it on the picking or
        compute it from your business rules.

        Accounts are resolved at runtime (can be != for dev/prod)
        """
        self.ensure_one()
        account = self._get_carrier_account()
        if not account:
            raise UserError(
                _(
                    "No account available with name '%s' "
                    "for this carrier" % self.carrier_id.delivery_type
                )
            )
        return account

    def _roulier_get_sender(self, package=None):
        """Sender of the picking (for the label).

        Return:
            (res.partner)
        """
        return self.company_id.partner_id

    def _roulier_get_label_format(self, account):
        """format of the label asked for carrier

        Return:
            label format (string)
        """
        return getattr(account, "%s_file_format" % self.delivery_type, None)

    def _roulier_get_receiver(self, package=None):
        """The guy whom the shippment is for.

        At home or at a distribution point, it's always
        the same receiver address.

        Return:
            (res.partner)
        """
        return self.partner_id

    def _roulier_get_shipping_date(self, package=None):
        """Choose a shipping date.

        By default, it's tomorrow."""
        tomorrow = date.today() + timedelta(1)
        return tomorrow

    def _roulier_convert_address(self, partner):
        """Convert a partner to an address for roulier.

        params:
            partner: a res.partner
        return:
            dict
        """
        address = {}
        extract_fields = [
            "company",
            "name",
            "zip",
            "city",
            "phone",
            "mobile",
            "email",
            "street2",
        ]
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
        if not address.get("company", False) and partner.parent_id.is_company:
            address["company"] = partner.parent_id.name
        # Roulier needs street1 (mandatory) not street
        address["street1"] = partner.street
        # Codet ISO 3166-1-alpha-2 (2 letters code)
        address["country"] = partner.country_id.code

        for tel in ["mobile", "phone"]:
            if address.get(tel):
                address[tel] = address[tel].replace(u"\u00A0", "").replace(" ", "")

        address["phone"] = address.get("mobile", address.get("phone"))

        return address

    def _roulier_get_from_address(self, package=None):
        sender = self._get_sender(package=package)
        return self._convert_address(sender)

    def _roulier_get_to_address(self, package=None):
        receiver = self._get_receiver(package=package)
        return self._convert_address(receiver)

    def _roulier_get_service(self, account, package=None):
        """Return a basic dict.

        The carrier implementation may add stuff
        like agency or options.

        return:
            dict
        """
        shipping_date = self._get_shipping_date(package)

        service = {
            "product": self.carrier_code,
            "shippingDate": shipping_date,
            "labelFormat": self._get_label_format(account),
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

        packages = self.package_ids
        if len(packages) == 0:
            raise UserError(_("No packages found for this picking"))
        elif len(packages) == 1:
            return packages.open_website_url()  # shortpath

        # display a list of pickings
        action = self.env.ref("stock.action_package_view").read()[0]
        action["domain"] = [("id", "in", packages.ids)]
        action["context"] = {"picking_id": self.id}
        return action
