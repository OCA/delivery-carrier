# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
import base64
import copy
import logging
from roulier.carriers.gls_fr.gls import Gls
from roulier.exception import CarrierError

from odoo import models, api, fields, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


def raise_exception(message):
    raise UserError(map_except_message(message))


def map_except_message(message):
    """ Allows to map vocabulary from external library
        to Odoo vocabulary in Exception message
    """
    model_mapping = {
        "shipper_country": "partner_id.country_id.code",
        "customer_id": "France or International field "
                       "(settings > config > carrier > GLS)",
    }
    for key, val in model_mapping.items():
        message = message.replace(key, val)
    return message


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_tracking_ref = fields.Char(copy=False)

    def _customize_gls_fr_picking(self):
        "Use this method to override gls picking"
        self.ensure_one()
        return True

    def _gls_get_to_address(self, package=None):
        address = self._roulier_get_to_address(package=package)
        address["country_code"] = address["country"]
        del address["country"]
        # TODO improve depending refactoring _roulier_convert_address()
        # specially keys: street2, company, phone, mobile
        addr = {}
        (addr["street"], addr["street2"],
         addr["street3"]) = self.partner_id._get_split_address(3, 35)
        if "company" not in address:
            address["company"] = self.partner_id.parent_id and \
                self.partner_id.parent_id.name or \
                self.partner_id.name
        address["company"] = address["company"][:35]
        address["name"] = address["name"][:35]
        address["mobile"] = self.partner_id.mobile or self.partner_id.phone
        return address

    def _gls_get_service(self, account, package=None):
        self.ensure_one()
        packages = self._get_packages_from_picking()
        gls_keys = ["carrier_gls_agency_id", "carrier_gls_customer_id"]
        config = {
            x.key: x.value
            for x in self.env["ir.config_parameter"].search(
                [("key", "in", gls_keys)])
        }
        return {
            "agencyId": config.get("carrier_gls_agency_id", ""),
            "customerId": config.get("carrier_gls_customer_id", ""),
            "shippingDate": date.today(),
            "shippingId": self.name,
            "intructions": self.note or "",
            "consignee_ref": self.name[:20],
            "reference_1": "",
            "reference_2": self.name[:20],
            "packages": packages,
            "parcel_total_number": len(packages),
        }

    @api.model
    def _prepare_pack_gls_fr(self, package, pack_number):
        return {
            "parcel_number_label": pack_number,
            "parcel_number_barcode": pack_number,
            "custom_sequence": self._get_sequence("gls"),
            "weight": "{0:05.2f}".format(package.weight)
        }

    def _generate_gls_fr_labels(self, service):
        """ Generate labels and write tracking numbers received """
        self.ensure_one()
        labels, traceability = [], []
        pack_number = 0
        account = self._get_account()
        service_infos = self._get_service(account)
        packages = service_infos.pop("packages")
        data = {
            'auth': {
                "login": account.account,
                "isTest": not self.carrier_id.prod_environment,
            },
            "service": service_infos,
            "from_address": self._get_sender(),
            "to_address": self._get_receiver(),
        }
        for package in packages:
            pack_number += 1
            params = copy.deepcopy(data)
            params['parcels'] = [
                self._prepare_pack_gls_fr(package, pack_number)]
            try:
                label = service.get_label(params)
            except CarrierError as e:
                message = e
                if hasattr(e, 'message'):
                    message = e.message
                raise UserError(message)
            except Exception as e:
                raise UserError(e)
            pack_vals = {"parcel_tracking": label["tracking_number"],
                         "carrier_id": self.carrier_id.id}
            package.write(pack_vals)
            _logger.info("package wrote")
            label_info = {
                "tracking_number": label["tracking_number"],
                "package_id": package.id,
                "file_type": "zpl2",
                "file": label["content"].encode(),
            }
            if label["tracking_number"]:
                label_info["name"] = "%s.zpl" % label["tracking_number"]
            # TODO define a better solution
            if self.company_id.country_id.code == "FR":
                labels.append(label_info)
            else:
                raise UserError(_(
                    "'GLS group' carrier is only available from France."
                    "Please update the country of your sender"))
            traceability.append(
                self._record_webservice_exchange(label, package))
        if self.carrier_id.debug_logging and traceability:
            self._save_traceability(traceability, label)
        self._customize_gls_fr_picking()
        return labels

    def _save_traceability(self, traceability, label):
        self.ensure_one()
        separator = "=*" * 40
        content = "\n\n%s\n\n\n" % separator
        content = content.join(traceability)
        content = (
            "Company: %s\nCompte France: %s \nCompte Etranger: %s \n\n\n") % (
            self.company_id.name or "",
            self.company_id.gls_login or "",
            self.company_id.gls_inter_login or "") + content
        data = {
            "name": "GLS_traceability.txt",
            "datas_fname": "GLS_traceability.txt",
            "res_id": self.id,
            "res_model": self._name,
            "datas": base64.b64encode(content.encode()),
            "type": "binary",
        }
        return self.env["ir.attachment"].create(data)

    def _record_webservice_exchange(self, label, pack):
        trac_infos = ""
        trac_infos = (
            "Sequence Colis GLS:\n====================\n%s \n\n"
            "Web Service Request:\n====================\n%s \n\n"
            "Web Service Response:\n=====================\n%s \n\n") % (
            "eeee",
            # pack["custom_sequence"],
            label.get("request_string"),
            label.get("response_string"))
        return trac_infos

    def get_zpl(self, service, delivery, address, pack):
        try:
            _logger.info(
                "GLS label generating for delivery '%s', pack '%s'",
                delivery["consignee_ref"], pack["parcel_number_label"])
            result = service.get_label(delivery, address, pack)
        except Exception as e:
            raise UserError(e.message)
        return result

    def _gls_generate_labels(self):
        """Create as many labels as packages or in self."""
        self.ensure_one()
        packages = self._get_packages_from_picking()
        # base_delivery_carrier_label module ensure packages is available
        self.number_of_packages = len(packages)
        self.carrier_tracking_ref = True  # display button in view
        return packages._generate_labels(self)

    @api.model
    def _get_sequence(self, label_name):
        sequence = self.env["ir.sequence"].next_by_code(
            "stock.picking_%s" % label_name)
        if not sequence:
            raise UserError(
                _("There is no sequence defined for the label '%s'")
                % label_name)
        return sequence

    def get_shipping_cost(self):
        return 0
