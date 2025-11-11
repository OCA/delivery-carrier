# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from unidecode import unidecode

from odoo import _, fields, models

from .correos_express_request import (
    CORREOS_EXPRESS_LABEL_TYPE,
    CORREOS_EXPRESS_PORTES,
    CORREOS_EXPRESS_SERVICE,
    CorreosExpressRequest,
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("correos_express", "Correos Express")],
        ondelete={"correos_express": "set default"},
    )
    correos_express_username = fields.Char()
    correos_express_password = fields.Char()
    correos_express_customer_code = fields.Char(string="Correos Express Client code")
    correos_express_sender_code = fields.Char(string="Correos Express Sender ID")
    correos_express_label_type = fields.Selection(
        string="Correos Express Label type", selection=CORREOS_EXPRESS_LABEL_TYPE
    )
    correos_express_product = fields.Selection(
        string="Correos Express Service",
        selection=CORREOS_EXPRESS_SERVICE,
        default="93",
    )
    correos_express_transport = fields.Selection(
        selection=CORREOS_EXPRESS_PORTES,
        default="P",
    )

    def correos_express_get_tracking_link(self, picking):
        tracking_url = "https://s.correosexpress.com/c?n={}"
        return tracking_url.format(picking.carrier_tracking_ref)

    def _format_correos_express_phone(self, phone):
        """Switch international prefix + to 00, as it's the one accepted by Correos
        Express, and remove spaces in the string for not overpassing the 15 chars limit.
        """
        return phone.replace("+", "00").replace(" ", "").replace("-", "")[:15]

    def _get_partner_streets(self, partner):
        streets = []
        if partner.street:
            streets.append(unidecode(partner.street))
        if partner.street2:
            streets.append(unidecode(partner.street2))
        return streets

    def _get_correos_express_receiver_info(self, picking):
        partner = picking.partner_id
        sending_partner = picking.picking_type_id.warehouse_id.partner_id
        streets = self._get_partner_streets(partner)
        phone = partner.mobile or partner.phone or ""
        national = partner.country_id.code == sending_partner.country_id.code
        return {
            "codDest": "",
            "nomDest": partner.name[:40] if partner.name else "",  # mandatory
            "nifDest": partner.vat or "",
            "dirDest": "".join(streets)[:300] if streets else "",  # mandatory
            "pobDest": partner.city[:40] if partner.city else "",  # mandatory
            "codPosNacDest": partner.zip if national else "",  # mandatory
            "paisISODest": partner.country_id.code or "",
            "codPosIntDest": partner.zip if not national else "",
            "contacDest": partner.name[:40] if partner.name else "",  # mandatory
            "telefDest": self._format_correos_express_phone(phone),  # mandatory
            "emailDest": partner.email[:75] if partner.email else "",
        }

    def _get_correos_express_sender_info(self, picking):
        partner = picking.picking_type_id.warehouse_id.partner_id
        streets = self._get_partner_streets(partner)
        return {
            "codRte": self.correos_express_customer_code,
            "nomRte": partner.name or "",
            "nifRte": partner.vat or "",
            "dirRte": "".join(streets)[:300],  # mandatory
            "pobRte": partner.city,  # mandatory
            "codPosNacRte": partner.zip,  # mandatory
            "paisISORte": partner.country_id.code or "",
            "codPosIntRte": "",
            "contacRte": partner.name or "",
            "telefRte": self._format_correos_express_phone(partner.phone or ""),
            "emailRte": partner.email or "",
        }

    def _get_package_info(self, picking):
        number_of_packages = picking.number_of_packages or 1
        package_list = []
        for i in range(0, number_of_packages):
            package_list.append(
                {
                    "ancho": "",
                    "observaciones": "",
                    "kilos": "",
                    "codBultoCli": "",
                    "codUnico": "",
                    "descripcion": "",
                    "alto": "",
                    "orden": i + 1,
                    "referencia": "",
                    "volumen": "",
                    "largo": "",
                }
            )
        return number_of_packages, package_list

    def _prepare_correos_express_shipping(self, picking):
        self.ensure_one()
        number_of_packages, package_list = self._get_package_info(picking)
        return dict(
            {
                "solicitante": self.correos_express_sender_code,  # mandatory
                "canalEntrada": "",
                "numEnvio": "",
                "ref": picking.name,
                "refCliente": picking.name,
                "fecha": fields.Datetime.now().strftime("%d%m%Y"),  # mandatory
                "contacOtrs": "",
                "telefOtrs": "",
                "emailOtrs": "",
                "observac": "",
                "numBultos": number_of_packages or 1,  # mandatory
                "kilos": "%.3f" % (picking.shipping_weight or 1),  # mandatory
                "volumen": "",
                "alto": "",
                "largo": "",
                "ancho": "",
                "producto": self.correos_express_product,  # mandatory
                "portes": self.correos_express_transport,  # mandatory
                "reembolso": "",
                "entrSabado": "",
                "seguro": "",
                "numEnvioVuelta": "",
                "listaBultos": package_list,
                "codDirecDestino": "",
                "password": "",
                "listaInformacionAdicional": [
                    {"tipoEtiqueta": self.correos_express_label_type, "etiquetaPDF": ""}
                ],
            },
            **self._get_correos_express_sender_info(picking),
            **self._get_correos_express_receiver_info(picking),
        )

    def correos_express_send_shipping(self, pickings):
        correos_express_request = CorreosExpressRequest(self)
        result = []
        is_pdf = self.correos_express_label_type != "2"
        for picking in pickings:
            vals = self._prepare_correos_express_shipping(picking)
            response = correos_express_request.create_shipment(vals)
            if not response:
                result.append(vals)
                continue
            vals.update(
                {
                    "tracking_number": response.get("datosResultado", ""),
                    "exact_price": 0,
                }
            )
            attachments = []
            if response.get("etiqueta"):
                # To decode the label with Base64 we need to decode it first
                # to binary and afterwards decode again to transform it
                # into a PDF or text document
                attachments = [
                    (
                        "correos_express_{}_{}.{}".format(
                            response.get("datosResultado", ""),
                            index + 1,
                            "pdf" if is_pdf else "txt",
                        ),
                        (
                            base64.b64decode(
                                base64.b64decode(label.get("etiqueta1", ""))
                            )
                            if is_pdf
                            else label.get("etiqueta2", "")
                        ),
                    )
                    for index, label in enumerate(response.get("etiqueta"))
                ]
            picking.message_post(body=_(""), attachments=attachments)
            result.append(vals)
        return result

    def _prepare_correos_express_tracking(self, picking):
        return {
            "codigoCliente": self.correos_express_customer_code,
            "dato": picking.carrier_tracking_ref,
        }

    def correos_express_tracking_state_update(self, picking):
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        correos_express_request = CorreosExpressRequest(self)
        result = correos_express_request.track_shipment(
            self._prepare_correos_express_tracking(picking)
        )
        if not result:
            return
        tracking_events = result.get("estadoEnvios", [])
        picking.tracking_state_history = "\n".join(
            [
                "{} {} - [{}] {}".format(
                    "{}:{}:{}".format(
                        t.get("horaEstado")[:2],
                        t.get("horaEstado")[2:-2],
                        t.get("horaEstado")[-2:],
                    ),
                    "{}/{}/{}".format(
                        t.get("fechaEstado")[:2],
                        t.get("fechaEstado")[2:-4],
                        t.get("fechaEstado")[4:],
                    ),
                    t.get("codEstado"),
                    t.get("descEstado"),
                )
                for t in tracking_events
            ]
        )
        tracking = tracking_events.pop()
        picking.tracking_state = "[{}] {}".format(
            tracking.get("codEstado"), tracking.get("descEstado")
        )

    def correos_express_cancel_shipment(self, pickings):
        for picking in pickings.filtered("carrier_tracking_ref"):
            picking.message_post(
                body=_(
                    "Correos Express does not provide a method to cancel a shipment "
                    "that has been registered. If you need to change some information "
                    "you, create a new shipment with a new label. This doesn't mean "
                    "that the shipment will be invoiced, this only happens if the "
                    "package is picked up and it enters the shipping stage"
                )
            )

    def _prepare_print_label(self, carrier_tracking_ref):
        return {
            "nenvio": carrier_tracking_ref,
            "tipo": self.correos_express_label_type,
            "keyCli": self.correos_express_customer_code,
        }

    def correos_express_get_label(self, carrier_tracking_ref):
        self.ensure_one()
        if not carrier_tracking_ref:
            return False
        correos_express_request = CorreosExpressRequest(self)
        labels = correos_express_request.print_shipment(
            self._prepare_print_label(carrier_tracking_ref)
        )
        return labels or False

    def correos_express_rate_shipment(self, order):
        """Not implemented with Correos, these values are so it works with websites"""
        return {
            "success": True,
            "price": self.product_id.lst_price,
            "error_message": _(
                "Correos Express API doesn't provide methods to compute "
                "delivery rates, so you should rely on another price method "
                "instead or override this one in your custom code."
            ),
            "warning_message": _(
                "Correos Express API doesn't provide methods to compute "
                "delivery rates, so you should rely on another price method "
                "instead or override this one in your custom code."
            ),
        }
