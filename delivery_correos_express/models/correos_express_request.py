# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)..

import logging

import requests

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
CORREOS_EXPRESS_LABEL_TYPE = [("1", "PDF"), ("2", "ZPL")]
CORREOS_EXPRESS_SERVICE = [
    ("26", "ISLAS EXPRESS"),
    ("61", "PAQ10"),
    ("62", "PAQ14"),
    ("63", "PAQ24"),
    ("66", "BALEARES"),
    ("67", "CANARIAS EXPRES"),
    ("68", "CANARIAS AEREO"),
    ("69", "CANARIAS MARITIMO"),
    ("90", "INTERNACIONAL ESTANDAR"),
    ("91", "INTERNACIONAL EXPRES"),
    ("92", "PAQ EMPRESA 14"),
    ("93", "EPAQ24"),
    ("27", "CAMPAÑA CEX"),
    ("53", "53 ENTREGA + MANIPULACION LOINEX"),
    ("54", "54 ENTREGA + RECOGIDA LOINEX"),
    ("55", "55 ENTREGA + RECOGIDA + MANIPULA LOINEX"),
    ("73", "CHRONO PORTUGAL OPTICA"),
    ("76", "PAQUETERIA OPTICAS"),
    ("77", "OPTICA PREPAGADO"),
]
CORREOS_EXPRESS_PORTES = [("P", "Paid"), ("D", "Due")]


TEST_PATH = "https://www.test.cexpr.es/wsps/"
PROD_PATH = "https://www.cexpr.es/wspsc/"


class CorreosExpressRequest:
    def __init__(self, carrier):
        self.carrier_id = carrier
        path = PROD_PATH if self.carrier_id.prod_environment else TEST_PATH
        self.urls = {
            "shipment": path + "apiRestGrabacionEnviok8s/json/grabacionEnvio",
            "label": path + "apiRestEtiquetaTransporte/json/etiquetaTransporte",
            "tracking": path + "apiRestSeguimientoEnviosk8s/json/seguimientoEnvio",
        }

    def _send_api_request(self, request_type, url, data=None, skip_auth=False):
        if data is None:
            data = {}
        result = {}
        try:
            auth = tuple()
            if not skip_auth:
                auth = tuple(
                    [
                        self.carrier_id.correos_express_username,
                        self.carrier_id.correos_express_password,
                    ]
                )
            if request_type == "GET":
                res = requests.get(url=url, auth=auth, timeout=60)
            elif request_type == "POST":
                _logger.debug(data)
                res = requests.post(url=url, auth=auth, json=data, timeout=60)
            else:
                raise UserError(
                    self.carrier_id.env._(
                        "Unsupported request type, please only use 'GET' or 'POST'"
                    )
                )
            result = res.json()
            correos_express_last_request = f"URL: {url}\nData: {data}"
            self.carrier_id.log_xml(
                correos_express_last_request, "correos_express_last_request"
            )
            self.carrier_id.log_xml(result, "correos_express_last_response")
            _logger.debug(res.json())
            res.raise_for_status()
        except requests.exceptions.Timeout as tmo:
            raise UserError(
                self.carrier_id.env._("Timeout: the server did not reply within 60s")
            ) from tmo
        except Exception as e:
            raise UserError(
                self.carrier_id.env._(
                    "{error}\n{result}".format(error=e, result=result if result else "")
                )
            ) from e
        return_code, message = self._check_for_error(result)
        if return_code != 0:
            raise UserError(
                self.carrier_id.env._(
                    "Correos Express Error: {return_code} {message}"
                ).format(return_code=return_code, message=message)
            )
        return res

    def _check_for_error(self, result):
        return_code = 999
        message = "Webservice ERROR."
        # shipment
        if not isinstance(result.get("codigoRetorno", "false"), str):
            return_code = result.get("codigoRetorno")
            message = result.get("mensajeRetorno") or ""
        # label
        if not isinstance(result.get("codErr", "false"), str):
            return_code = result.get("codErr")
            message = result.get("desErr") or ""
        # tracking
        if not isinstance(result.get("error", "false"), str):
            return_code = result.get("error")
            message = result.get("mensajeError") or ""
        return return_code, message

    def create_shipment(self, vals):
        res = self._send_api_request(
            request_type="POST", url=self.urls["shipment"], data=vals
        )
        return res.json()

    def print_shipment(self, vals):
        res = self._send_api_request(
            request_type="POST", url=self.urls["label"], data=vals
        )
        return res.json().get("listaEtiquetas", [])

    def track_shipment(self, vals):
        res = self._send_api_request(
            request_type="POST", url=self.urls["tracking"], data=vals
        )
        return res.json()
