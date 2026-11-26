# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from urllib.parse import quote

import requests

from odoo import fields, models
from odoo.exceptions import UserError

from . import dpd_api


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dpd_pt", "DPD Portugal")], ondelete={"dpd_pt": "cascade"}
    )
    dpd_pt_subaccount = fields.Char(
        string="DPD Sub-Account",
        size=8,
        help="8-digit DPD sub-account used to register shipments.",
    )
    dpd_pt_sender_id = fields.Many2one(
        "res.partner",
        string="DPD Sender Contact",
        help="Contact person of the shipper used on DPD labels.",
    )
    dpd_pt_price = fields.Float(
        string="DPD Agreed Price",
        digits="Product Price",
        help="Price agreed with DPD. The DPD API does not provide rating; "
        "this value is used for shipping costs and rate requests.",
    )
    dpd_pt_label_format = fields.Selection(
        [
            ("1", "A4 - one label"),
            ("2", "A4 - two labels"),
            ("3", "Thermal 10 x 15 cm (ZPL)"),
        ],
        string="DPD Label Format",
        default="1",
        required=True,
    )
    dpd_pt_predict_enabled = fields.Boolean(
        string="DPD Predict Delivery",
        help="Request DPD Predict delivery service on shipments.",
    )
    dpd_pt_hide_recipient_phone = fields.Boolean(
        string="Hide Recipient Phone on Label",
    )
    dpd_pt_hide_recipient_email = fields.Boolean(
        string="Hide Recipient Email on Label",
    )

    # ------------------------------------------------------------------
    # Carrier interface
    # ------------------------------------------------------------------

    def _dpd_pt_connection(self, picking):
        account = picking._get_carrier_account()
        required = (
            account,
            account.account,
            account.password,
            account.dpd_pt_client_id,
            account.dpd_pt_client_secret,
        )
        if not all(required):
            raise UserError(
                self.env._(
                    "Configure the DPD Portugal carrier account "
                    "(user, password, OAuth client ID and secret)."
                )
            )
        return account, ("prod" if self.prod_environment else "test")

    def dpd_pt_rate_shipment(self, order):
        self.ensure_one()
        # The DPD API has no rating endpoint; return the agreed price.
        return {
            "success": True,
            "price": self.dpd_pt_price,
            "error_message": False,
            "warning_message": False,
        }

    def dpd_pt_send_shipping(self, pickings):
        self.ensure_one()
        return [self._dpd_pt_send_picking(picking) for picking in pickings]

    def dpd_pt_get_tracking_link(self, picking):
        if not self.prod_environment or not picking.carrier_tracking_ref:
            return False
        reference = picking.carrier_tracking_ref.split(",")[0].strip()
        return dpd_api.tracking_url(reference)

    def dpd_pt_cancel_shipment(self, pickings):
        self.ensure_one()
        for picking in pickings:
            self._dpd_pt_cancel_picking(picking)

    # ------------------------------------------------------------------
    # Shipment dispatch
    # ------------------------------------------------------------------

    def _dpd_pt_send_picking(self, picking):
        account, environment = self._dpd_pt_connection(picking)
        payload = self._dpd_pt_prepare_shipment_data(picking)
        result = self._dpd_pt_request(
            account, environment, "create", payload, picking.name
        )
        if not isinstance(result, dict):
            raise UserError(
                self.env._(
                    "DPD did not return shipment data. Check the shipment in "
                    "the DPD portal before retrying."
                )
            )
        numbers = dpd_api.guide_numbers(
            self.env, result.get("guias_seur") or result.get("num_guia")
        )
        picking.carrier_tracking_ref = ",".join(numbers)
        self._dpd_pt_store_label(picking, result, numbers[0], account, environment)
        return {
            "exact_price": self.dpd_pt_price,
            "tracking_number": picking.carrier_tracking_ref,
        }

    def _dpd_pt_cancel_picking(self, picking):
        if not picking.carrier_tracking_ref:
            return
        account, environment = self._dpd_pt_connection(picking)
        reference = picking.carrier_tracking_ref.split(",")[0].strip()
        result = self._dpd_pt_request(account, environment, "lookup", {}, reference)
        entries = result if isinstance(result, list) else [result]
        expedition_ids = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_guides = entry.get("num_guia")
            if entry_guides and reference not in dpd_api.guide_numbers(
                self.env, entry_guides
            ):
                continue
            if entry.get("id") is None:
                raise UserError(
                    self.env._(
                        "DPD returned a shipment without an expedition ID; "
                        "cancel it in the DPD portal."
                    )
                )
            expedition_ids.append(str(entry["id"]))
        expedition_ids = list(dict.fromkeys(expedition_ids))
        if not expedition_ids:
            raise UserError(
                self.env._(
                    "No DPD expedition found for %s; cancel it in the DPD portal.",
                    reference,
                )
            )
        self._dpd_pt_request(
            account, environment, "cancel", {"ids": expedition_ids}, picking.name
        )

    # ------------------------------------------------------------------
    # API layer
    # ------------------------------------------------------------------

    def _dpd_pt_request(self, account, environment, key, payload, identifier):
        verb, path = dpd_api.METHODS[key]
        url = dpd_api.URLS[environment] + "/" + path
        if path.endswith("/"):
            identifier = str(identifier or "").strip()
            if not identifier:
                raise UserError(self.env._("Enter a valid DPD guide number."))
            url += quote(identifier, safe="")
        token = self._dpd_pt_get_token(account, environment)
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
        }
        try:
            if verb == "GET":
                response = requests.get(
                    url, headers=headers, timeout=(10, 60), allow_redirects=False
                )
            else:
                if payload is None:
                    response = requests.post(
                        url,
                        headers=headers,
                        timeout=(10, 60),
                        allow_redirects=False,
                    )
                else:
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=(10, 60),
                        allow_redirects=False,
                    )
        except requests.RequestException:
            raise UserError(
                self.env._(
                    "No conclusive response from DPD. Check the shipment in "
                    "the DPD portal before retrying."
                )
            ) from None
        if (
            response.status_code == 200
            and key == "label"
            and response.content.startswith(b"%PDF-")
        ):
            return {"pdf": base64.b64encode(response.content).decode()}
        try:
            data = response.json()
        except ValueError:
            content = None
            if key == "zpl" and response.status_code == 200:
                try:
                    content = response.content.decode()
                except UnicodeDecodeError:
                    content = None
            if content:
                return {"zpl": content}
            raise UserError(
                self.env._(
                    "DPD returned an unreadable response (HTTP %s). "
                    "Check the shipment in the DPD portal before retrying.",
                    response.status_code,
                )
            ) from None
        if isinstance(data, str) and key == "zpl" and response.status_code == 200:
            return {"zpl": data}
        if not isinstance(data, dict):
            raise UserError(self.env._("DPD returned an invalid response."))
        try:
            status = int(data.get("status_code", response.status_code))
        except (TypeError, ValueError):
            raise UserError(
                self.env._("DPD returned an invalid status code.")
            ) from None
        if response.status_code not in (200, 201) or status not in (200, 201):
            raise UserError(
                self.env._(
                    "DPD (%(code)s): %(reason)s",
                    code=status,
                    reason=self._dpd_pt_safe_error(account, data),
                )
            )
        return data["result"] if "result" in data else data

    def _dpd_pt_safe_error(self, account, data):
        message = str(
            data.get("message") or data.get("error") or "Request not confirmed"
        )
        account = account.sudo()
        for secret in (
            account.password,
            account.dpd_pt_client_secret,
            account.account,
        ):
            if secret:
                message = message.replace(secret, "[hidden]")
        return message[:600]

    def _dpd_pt_get_token(self, account, environment):
        url = dpd_api.URLS[environment] + "/oauth/token"
        status_code = None
        token = None
        try:
            response = requests.post(
                url,
                data={
                    "username": account.account,
                    "password": account.password,
                    "client_id": account.dpd_pt_client_id,
                    "client_secret": account.dpd_pt_client_secret,
                    "grant_type": "password",
                },
                timeout=(10, 45),
                allow_redirects=False,
            )
            status_code = response.status_code
            data = response.json()
            result = data.get("result") or data if isinstance(data, dict) else {}
            token = result.get("access_token") if isinstance(result, dict) else None
        except (requests.RequestException, ValueError):
            token = None
        if status_code not in (200, 201) or not token:
            raise UserError(
                self.env._(
                    "DPD authentication failed. Check the carrier account "
                    "credentials and OAuth client."
                )
            )
        return token

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def _dpd_pt_store_label(self, picking, result, reference, account, environment):
        zpl_label = self.dpd_pt_label_format == "3"
        label_key = "zpl" if zpl_label else "pdf"
        value = self._dpd_pt_label_value(result, label_key)
        if not value:
            try:
                fetched = self._dpd_pt_request(
                    account,
                    environment,
                    "zpl" if zpl_label else "label",
                    None if zpl_label else {},
                    reference,
                )
                value = self._dpd_pt_label_value(fetched, label_key)
            except UserError:
                value = None
        try:
            raw = dpd_api.zpl_bytes(value) if zpl_label else dpd_api.pdf_bytes(value)
        except (ValueError, TypeError):
            # The expedition already exists at DPD; do not raise or the
            # shipment would be registered twice on retry.
            picking.message_post(
                body=self.env._(
                    "DPD shipment %(reference)s was registered, but no valid "
                    "%(label_type)s label was returned. Download it from the "
                    "DPD portal.",
                    reference=reference,
                    label_type="ZPL" if zpl_label else "PDF",
                )
            )
            return
        attachment = picking.env["ir.attachment"].create(
            {
                "name": f"DPD_{reference}.{'zpl' if zpl_label else 'pdf'}",
                "raw": raw,
                "res_model": "stock.picking",
                "res_id": picking.id,
                "mimetype": "application/octet-stream"
                if zpl_label
                else "application/pdf",
            }
        )
        picking.message_post(
            body=self.env._("DPD Portugal label for %s.", reference),
            attachment_ids=[attachment.id],
        )

    def _dpd_pt_label_value(self, result, key):
        if isinstance(result, str):
            return result
        if not isinstance(result, dict):
            return None
        if result.get(key):
            return result[key]
        if key == "zpl":
            return result.get("zpl_base64")
        return None

    # ------------------------------------------------------------------
    # Payload
    # ------------------------------------------------------------------

    def _dpd_pt_prepare_shipment_data(self, picking):
        if not self.dpd_pt_subaccount:
            raise UserError(self.env._("Set the DPD sub-account on the carrier."))
        sender = self.dpd_pt_sender_id or picking.company_id.partner_id
        recipient = picking.partner_id
        warehouse = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        if not recipient.country_id:
            raise UserError(self.env._("Set the country on the recipient."))
        weight = round(picking.shipping_weight, 2)
        if weight <= 0:
            raise UserError(self.env._("Enter the real weight of the shipment."))
        if weight > 999.99:
            raise UserError(self.env._("DPD accepts shipment weights up to 999.99."))
        number_of_volumes = picking.number_of_packages or 1
        if number_of_volumes <= 0:
            raise UserError(self.env._("The number of parcels must be positive."))
        cod_amount = picking.dpd_pt_cod_amount or 0.0
        if cod_amount < 0:
            raise UserError(
                self.env._("The DPD cash on delivery amount cannot be negative.")
            )
        if cod_amount and picking.company_id.currency_id.name != "EUR":
            raise UserError(
                self.env._("DPD cash on delivery must be declared in euros.")
            )
        reference = dpd_api.text(
            self.env,
            picking.name,
            self.env._("Reference / transport document"),
            16,
        )
        at_code = (
            dpd_api.text(
                self.env,
                getattr(picking, "l10n_pt_delivery_code", False),
                self.env._("AT code"),
                11,
                required=False,
            )
            or None
        )
        zpl_label = self.dpd_pt_label_format == "3"
        return {
            "sub_account": {"code": self.dpd_pt_subaccount},
            "sender": self._dpd_pt_prepare_contact_data(sender, required_email=True),
            "shipper": self._dpd_pt_prepare_shipper_data(warehouse),
            "recipient": {
                "id": None,
                "name": dpd_api.text(
                    self.env,
                    recipient.name,
                    self.env._("Recipient name"),
                    32,
                ),
                "client_code": None,
                "save": False,
            },
            "address": self._dpd_pt_prepare_recipient_address_data(recipient),
            "contact": self._dpd_pt_prepare_contact_data(recipient),
            "destinatario_usar_endereco_pickup": False,
            "opcoes_servico_predict_para_entrega": self.dpd_pt_predict_enabled,
            "encomenda_referencia": reference,
            "opcoes_servico_codigo_at": at_code,
            "encomenda_observacao": None,
            "expedition_date": fields.Date.context_today(self).isoformat(),
            "encomenda_peso_envio": weight,
            "encomenda_num_volumes": number_of_volumes,
            "opcoes_servico_enviar_a_cobranca": cod_amount > 0,
            "opcoes_servico_montante": round(cod_amount, 2) if cod_amount else None,
            "etiqueta_hide_nome": False,
            "etiqueta_hide_telemovel": self.dpd_pt_hide_recipient_phone,
            "etiqueta_hide_email": self.dpd_pt_hide_recipient_email,
            "etiqueta_formato": {"id": int(self.dpd_pt_label_format)},
            "etiqueta_enviar_etiqueta_por_email": False,
            "pdf_response": not zpl_label,
            "zpl_response": zpl_label,
            "qr_response": False,
        }

    def _dpd_pt_prepare_contact_data(self, partner, required_email=False):
        phone_number = phone_code = None
        if partner.phone:
            phone_number, phone_code = dpd_api.phone(
                self.env, partner.phone, partner.country_id.code
            )
        if "mobile" in partner._fields:
            mobile_value = partner.mobile
        else:
            mobile_value = partner.phone
        mobile_number, mobile_code = dpd_api.phone(
            self.env, mobile_value, partner.country_id.code
        )
        return {
            "id": None,
            "name": dpd_api.text(
                self.env, partner.name, self.env._("Contact name"), 32
            ),
            "phone": phone_number,
            "phone_code": phone_code,
            "mobile": mobile_number,
            "mobile_code": mobile_code,
            "email": dpd_api.text(
                self.env,
                partner.email,
                self.env._("Contact email"),
                50,
                required=required_email,
            )
            or None,
            "save": False,
        }

    def _dpd_pt_prepare_shipper_data(self, partner):
        if not partner or not partner.country_id:
            return None
        return {
            "name": dpd_api.text(
                self.env,
                partner.name,
                self.env._("Warehouse name"),
                32,
                required=False,
            )
            or None,
            "address": dpd_api.text(
                self.env,
                " ".join(filter(None, [partner.street, partner.street2])),
                self.env._("Warehouse address"),
                64,
                required=False,
            )
            or None,
            "zip_code": dpd_api.postcode(
                self.env, partner.zip, partner.country_id.code, required=False
            )
            or None,
            "location": dpd_api.text(
                self.env,
                partner.city,
                self.env._("Warehouse location"),
                26,
                required=False,
            )
            or None,
            "country": {"id": partner.country_id.code},
        }

    def _dpd_pt_prepare_recipient_address_data(self, partner):
        country = partner.country_id.code
        return {
            "id": None,
            "country": {"id": country, "iso2": country},
            "address": dpd_api.text(
                self.env,
                " ".join(filter(None, [partner.street, partner.street2])),
                self.env._("Recipient address"),
                64,
            ),
            "zip_code": dpd_api.postcode(self.env, partner.zip, country),
            "location": dpd_api.text(
                self.env, partner.city, self.env._("Recipient location"), 26
            ),
            "save": False,
        }
