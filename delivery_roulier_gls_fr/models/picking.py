# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
import base64
import copy
import logging
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

    def _gls_fr_get_to_address(self, package=None):
        address = self._roulier_get_to_address(package=package)
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

    def _gls_fr_get_service(self, account, package=None):
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
            "parcel_total_number": len(packages),
        }

            # TODO traçability part if needed
#            traceability.append(
#                self._record_webservice_exchange(label, package))
#        if self.carrier_id.debug_logging and traceability:
#            self._save_traceability(traceability, label)

#    def _save_traceability(self, traceability, label):
#        self.ensure_one()
#        separator = "=*" * 40
#        content = "\n\n%s\n\n\n" % separator
#        content = content.join(traceability)
#        content = (
#            "Company: %s\nCompte France: %s \nCompte Etranger: %s \n\n\n") % (
#            self.company_id.name or "",
#            self.company_id.gls_login or "",
#            self.company_id.gls_inter_login or "") + content
#        data = {
#            "name": "GLS_traceability.txt",
#            "datas_fname": "GLS_traceability.txt",
#            "res_id": self.id,
#            "res_model": self._name,
#            "datas": base64.b64encode(content.encode()),
#            "type": "binary",
#        }
#        return self.env["ir.attachment"].create(data)
#
#    def _record_webservice_exchange(self, label, pack):
#        trac_infos = ""
#        trac_infos = (
#            "Sequence Colis GLS:\n====================\n%s \n\n"
#            "Web Service Request:\n====================\n%s \n\n"
#            "Web Service Response:\n=====================\n%s \n\n") % (
#            "eeee",
#            # pack["custom_sequence"],
#            label.get("request_string"),
#            label.get("response_string"))
#        return trac_infos

    def get_shipping_cost(self):
        return 0
