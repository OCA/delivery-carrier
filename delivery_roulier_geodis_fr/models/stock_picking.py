# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, fields, models
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import CarrierError, InvalidApiInput
except ImportError:
    _logger.debug("Cannot `import roulier`.")


GEODIS_DEFAULT_PRIORITY = {
    "MES": "3",
    "MEI": "3",
    "CXI": "1",
    "CX": "1",
    "EEX": "1",
}

GEODIS_DEFAULT_TOD = {
    "MES": "P",
    "MEI": "DAP",
    "CXI": "P",
    "EEX": "DAP",
}

ADDRESS_ERROR_CODES = ["C0041", "C0042", "C0044", "C0045", "C0047", "T0023"]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    geodis_shippingid = fields.Char(
        help="Shipping Id in Geodis terminology", copy=False
    )

    def _geodis_fr_convert_address(self, partner):
        """Truncate address and name to 35 chars."""
        address = self._roulier_convert_address(partner) or {}
        # get_split_adress from partner_address_split module
        streets = partner._get_split_address(3, 35)
        address["street1"], address["street2"], address["street3"] = streets
        for field in ("name", "city"):
            address[field] = address[field][0:35]
        return address

    def _geodis_fr_get_priority(self, package):
        """Define options for the shippment."""
        return GEODIS_DEFAULT_PRIORITY.get(self.carrier_code, "")

    def _geodis_fr_get_options(self, package):
        """Compact geodis options.

        Options are passed as string. it obey some custom
        binding like RDW + AAO = AWO.
        It should be implemented here. For the moment, only
        one option can be passed.
        """
        options = self._roulier_get_options(package)
        actives = [option for option in options.keys() if options[option]]
        return actives and actives[0] or ""

    def _geodis_fr_get_notifications(self, package):
        options = self._get_options(package)
        recipient = self._convert_address(self._get_receiver(package))
        if "RDW" in options:
            if recipient.get("email"):
                if recipient["phone"]:
                    return "M"
                else:
                    return "P"
            else:
                if recipient.get("phone"):
                    return "S"
                else:
                    raise UserError(_("Can't set up a rendez-vous wihout mail or tel"))

    def _geodis_fr_get_service(self, account, package=None):
        service = self._roulier_get_service(account, package=package)
        agency = self._get_carrier_agency()

        service["option"] = self._get_options(package)
        service["notifications"] = self._geodis_fr_get_notifications(package)
        service["customerId"] = account.geodis_fr_customer_id
        service["agencyId"] = agency.external_reference
        service["hubId"] = agency.geodis_fr_hub_id
        self._gen_shipping_id()  # explicit generation
        service["shippingId"] = self.geodis_shippingid
        return service

    def _geodis_fr_prepare_edi(self):
        """Return a list."""
        self.ensure_one()
        picking = self

        packages = picking.package_ids
        parcels = [pack._get_edi_pack_vals() for pack in packages]

        return {
            "product": picking.carrier_id.code,
            "productOption": picking._get_options(None),
            "productPriority": picking._geodis_fr_get_priority(None),
            "notifications": picking._geodis_fr_get_notifications(None),
            "productTOD": GEODIS_DEFAULT_TOD[picking.carrier_code],
            "to_address": self._convert_address(picking._get_receiver(None)),
            "reference1": picking.origin or picking.group_id.name or picking.name,
            "reference2": "",
            "reference3": "",
            "shippingId": picking.geodis_shippingid,
            "parcels": parcels,
        }

    def _geodis_fr_get_address_proposition(self, raise_address=True):
        # check address
        self.ensure_one()
        payload = {}
        receiver = self._get_receiver()
        account = self._get_account()
        payload["auth"] = self._get_auth(account)
        payload["to_address"] = self._convert_address(receiver)
        payload["service"] = {"is_test": not self.carrier_id.prod_environment}
        addresses = []
        try:
            # api call
            addresses = roulier.get(self.delivery_type, "validate_address", payload)
        except InvalidApiInput as e:
            raise UserError(
                self.env["stock.quant.package"]._invalid_api_input_handling(payload, e)
            ) from e
        except CarrierError as e:
            errors = e.args and e.args[0]
            if (
                errors
                and errors[0].get("id")
                and not raise_address
                and errors[0].get("id") in ADDRESS_ERROR_CODES
            ):
                return addresses
            else:
                package = self.env["stock.quant.package"].new({})
                package.carrier_id = self.carrier_id
                raise UserError(package._carrier_error_handling(payload, e)) from e
        return addresses

    def _geodis_fr_check_address(self):
        self.ensure_one()
        addresses = self._geodis_fr_get_address_proposition()
        return len(addresses) == 1

    def _gen_shipping_id(self):
        """Generate a shipping id.

        Shipping id is persisted on the picking and it's
        calculated from a sequence since it should be
        8 char long and unique for at least 1 year
        """

        def gen_id():
            sequence = self.env["ir.sequence"].next_by_code("geodis.nrecep.number")
            # this is prefixed by year_ so we split it befor use
            year, number = sequence.split("_")
            # pad with 0 to build an 8digits number (string)
            return "%08d" % int(number)

        for picking in self:
            picking.geodis_shippingid = picking.geodis_shippingid or gen_id()
        return True

    def _geodis_fr_update_tracking(self):
        success_pickings = self.env["stock.picking"]
        for rec in self:
            packages = rec.package_ids
            account = rec._geodis_fr_get_auth_tracking()
            payload = {
                "auth": account,
                "tracking": {"shippingId": rec.geodis_shippingid},
            }
            ret = roulier.get(rec.delivery_type, "get_tracking_list", payload)

            if len(ret) != 1:
                _logger.info("Geodis tracking not found. Picking %s" % rec.id)
                continue
            # multipack not implemented yet
            data = ret[0]
            rec.write({"carrier_tracking_ref": data["tracking"]["trackingCode"]})
            packages.write(
                {
                    "parcel_tracking_uri": data["tracking"]["publicUrl"],
                    "parcel_tracking": data["tracking"]["trackingCode"],
                }
            )
            success_pickings |= rec
        return success_pickings

    def _geodis_fr_get_auth_tracking(self):
        """Because it's not the same credentials than
        get_label."""

        account = self._geodis_fr_get_account_tracking()
        auth = {
            "login": account.account,
            "password": account.password,
        }
        return auth

    def _geodis_fr_get_account_tracking(self):
        """Return an 'account'.

        By default, the first account encoutered for this type.
        Depending on your case, you may store it on the picking or
        compute it from your business rules.

        """
        account = self.env["carrier.account"].search(
            [
                ("delivery_type", "=", self.carrier_id.delivery_type),
                ("geodis_fr_tracking_account", "=", True),
            ],
            limit=1,
        )
        return account

    def _get_carrier_account_domain(self):
        domain = super()._get_carrier_account_domain()
        domain.append(("geodis_fr_tracking_account", "!=", True))
        return domain
