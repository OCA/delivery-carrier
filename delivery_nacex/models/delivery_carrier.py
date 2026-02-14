import base64
import logging

import requests

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

NACEX_API_URL = "https://pda.nacex.com/nacex_ws/ws"


class NacexDeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("nacex", "NACEX")],
        ondelete={"nacex": "set default"},
    )
    nacex_agency_code = fields.Char(string="Agency Code", help="NACEX agency code")
    nacex_customer_code = fields.Char(string="Customer Code", help="NACEX customer code")
    nacex_service_code = fields.Selection(
        [
            ("01", "NACEX 10:00H"),
            ("02", "NACEX 12:00H"),
            ("03", "INTERDIA"),
            ("04", "PLUS BAG 1"),
            ("05", "PLUS BAG 2"),
            ("06", "SUITCASE"),
            ("07", "VALIJA ROUND TRIP"),
            ("08", "NACEX 19:00H"),
            ("09", "URBAN BRIDGE"),
            ("10", "RETURN ALBARAN CUSTOMER"),
            ("11", "NACEX 08:30H"),
            ("12", "HEEL RETURN"),
            ("14", "RETURN PLUS BAG 1"),
            ("15", "RETURN PLUS BAG 2"),
            ("17", "RETURN E-NACEX"),
            ("21", "NACEX SATURDAY"),
            ("22", "CANARY ISLANDS"),
            ("24", "CANARY ISLANDS 24H"),
            ("26", "PLUS PACK"),
            ("27", "E-NACEX"),
            ("28", "PREMIUM"),
            ("29", "NX-SHOP GREEN"),
            ("30", "NX-SHOP ORANGE"),
            ("31", "E-NACEX SHOP"),
            ("33", "C@MBIO"),
            ("48", "CANARY ISLANDS 48H"),
            ("88", "RIGHT NOW"),
            ("90", "NACEX.SHOP"),
            ("91", "SWAP"),
            ("95", "RETURN SWAP"),
            ("96", "DEV. ORIGIN"),
        ],
        help="Enter your service code",
    )
    nacex_carriage_code = fields.Selection(
        [("O", "Origen"), ("D", "Destino"), ("T", "Tercera")],
        help="Enter your Nacex carriage code",
    )
    nacex_packaging_code = fields.Selection(
        [("0", "Docs"), ("1", "Bag"), ("2", "Pag")],
    )
    nacex_with_return = fields.Boolean(string="With Return?")

    def nacex_rate_shipment(self, order):
        return {
            "success": True,
            "price": 0.0,
            "error_message": False,
            "warning_message": "NACEX does not provide rate estimation.",
        }

    def nacex_get_tracking_link(self, picking):
        """Return NACEX tracking link for the given picking.

        :param picking: stock.picking record
        :return: tracking URL or False
        """
        if picking.carrier_tracking_ref:
            return (
                "https://www.nacex.com/seguimientoDetalle.do"
                "?agencia_origen=%(agencia)s&numero_albaran=%(number)s"
            ) % {
                "agencia": self._nacex_get_agency_code(picking),
                "number": picking.carrier_tracking_ref,
            }
        return False

    def _nacex_get_agency_code(self, picking):
        """Return the NACEX agency code for the given picking.

        Resolves the agency via delivery_carrier_agency if available,
        falling back to the nacex_agency_code field on the carrier.

        :param picking: stock.picking record
        :return: agency code string
        """
        agency = picking._get_carrier_agency()
        if agency and agency.external_reference:
            return agency.external_reference
        return self.nacex_agency_code or ""

    def _nacex_request(self, method, data, picking):
        """Execute a NACEX API request and return the response text.

        :param method: NACEX API method name (e.g. 'putExpedicion')
        :param data: dict of key/value pairs for the NACEX data parameter
        :param picking: stock.picking record (used to resolve the account)
        :return: response text
        """
        account = picking._get_carrier_account()
        if not account or not account.account or not account.password:
            raise UserError(self.env._("Please configure a NACEX carrier account."))
        data_str = "|".join(f"{k}={v}" for k, v in data.items())
        params = {
            "method": method,
            "data": data_str,
            "user": account.account,
            "pass": account.password,
        }
        _logger.info("NACEX %s request: data=%s", method, data_str)

        try:
            response = requests.get(
                NACEX_API_URL,
                params=params,
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:
            raise UserError(
                self.env._("NACEX connection error: %(error)s", error=exc)
            ) from exc

        if response.status_code not in (200, 201):
            raise UserError(
                self.env._(
                    "NACEX API error (HTTP %(code)s): %(text)s",
                    code=response.status_code,
                    text=response.text,
                )
            )

        if response.text.startswith("ERROR"):
            raise UserError(
                self.env._(
                    "NACEX %(method)s error: %(text)s",
                    method=method,
                    text=response.text,
                )
            )

        _logger.info("NACEX %s response OK", method)
        return response.text

    def _nacex_put_expedicion(self, picking):
        """Create an expedition on NACEX and return the raw response text.

        :param picking: single stock.picking record
        :return: raw response string (e.g. "391950567|7244/10865047|VERDE")
        """
        self.ensure_one()
        recipient = picking.partner_id
        shipper = picking.picking_type_id.warehouse_id.partner_id

        if not shipper.zip or not shipper.city or not shipper.country_id:
            raise UserError(self.env._("Please define a correct sender address."))
        if not recipient.zip or not recipient.city or not recipient.country_id:
            raise UserError(self.env._("Please define a correct recipient address."))

        if picking.package_ids:
            package_count = str(len(picking.package_ids))
            total_weight = sum(picking.package_ids.mapped("shipping_weight"))
        else:
            package_count = str(picking.number_of_packages or 1)
            total_weight = picking.shipping_weight or 0.0

        data = {
            "del_cli": self._nacex_get_agency_code(picking),
            "num_cli": self.nacex_customer_code or "",
            "tip_ser": self.nacex_service_code or "",
            "tip_cob": self.nacex_carriage_code or "",
            "ref_cli": picking.origin or "",
            "tip_env": self.nacex_packaging_code or "",
            "bul": package_count,
            "kil": total_weight,
            "nom_ent": recipient.name or "",
            "dir_ent": (recipient.street or "").replace("#", " "),
            "pais_ent": recipient.country_id.code or "",
            "cp_ent": (recipient.zip or "").replace("-", "").replace("/", ""),
            "pob_ent": recipient.city or "",
            "tel_ent": recipient.phone or "",
            "obs1": "observaciones",
            "cp_rec": (shipper.zip or "").replace("-", "").replace("/", ""),
        }
        
        # Add return flag if configured on picking (falls back to carrier default)
        if picking.nacex_with_return:
            data["ret"] = "S"
            
        return self._nacex_request("putExpedicion", data, picking)

    def nacex_send_shipping(self, pickings):
        """Send shipment to NACEX and return label + tracking info.

        :param pickings: recordset of stock.picking
        :return: list of dicts with 'exact_price' and 'tracking_number'
        """
        self.ensure_one()
        res = []
        for picking in pickings:
            expedicion = self._nacex_put_expedicion(picking)
            parts = expedicion.split("|")
            tracking_number = parts[1].split("/")[1]
            label_text = self._nacex_request(
                "getEtiqueta",
                {
                    "codExp": parts[0],
                    "modelo": "PDF_B",
                },
                picking,
            )

            # Decode base64 label (NACEX uses URL-safe base64 variant)
            label_b64 = label_text.replace("-", "+").replace("_", "/").replace("*", "=")
            pdf_label_data = base64.b64decode(label_b64)
            picking.message_post(
                body=self.env._(
                    "<b>Tracking Number:</b> %(number)s",
                    number=tracking_number,
                ),
                attachments=[(f"{tracking_number}.pdf", pdf_label_data)],
            )
            res.append(
                {
                    "exact_price": 0.0,
                    "tracking_number": tracking_number,
                }
            )
        return res

    def nacex_cancel_shipment(self, pickings):
        raise UserError(self.env._("NACEX cancel shipment API is not available."))
