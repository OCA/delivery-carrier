# Copyright 2022 Impulso Diagonal - Javier Colmeiro
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError

from .sending_master_data import SENDING_COUNTRY_CODES, SENDING_SERVICES
from .sending_request import SendingRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("sending", "Sending")])
    sending_access_key = fields.Char(string="Access Key", help="sending Access Key")
    sending_user = fields.Char(string="User")
    sending_service = fields.Selection(
        selection=SENDING_SERVICES,
        string="Sending Service",
        help="Set the contracted Sending Service",
        default="01",
    )
    sending_file_format = fields.Selection(
        selection=[("ZPL", "ZPL"), ("PDF", "PDF")], default="ZPL", string="File format",
    )

    def _sending_request(self):
        return SendingRequest(
            uidcustomer=self.sending_user, uidpass=self.sending_access_key,
        )

    def _sending_check_error(self, response):
        if (
            response[:2] != "OK"
            and response[:2] != "TE"
            and not self.env.context.get("skip_errors")
        ):
            raise UserError(
                _("Sending returned an error.\nError:\n{}").format(response)
            )

    def _prepare_sending_shipping(self, picking):
        """Convert picking values for asm api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        # A picking can be delivered from any warehouse
        sender_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        consignee = picking.partner_id
        if consignee.country_id.code not in SENDING_COUNTRY_CODES.keys():
            raise UserError(_("Delivery country not implemented with this carrier!"))
        return {
            "date": fields.Date.today().strftime("%d/%m/%Y"),
            "uidcustomername": sender_partner.name,
            "uidcustomeraddress": "%s%s"
            % (
                sender_partner.street or "",
                " " + sender_partner.street2 if sender_partner.street2 else "",
            ),
            "uidcustomercountry": SENDING_COUNTRY_CODES[sender_partner.country_id.code],
            "uidcustomerzip": sender_partner.zip,
            "uidcustomercity": sender_partner.city,
            "clientname": consignee.name,
            "clientaddress": "%s%s"
            % (
                consignee.street or "",
                " " + consignee.street2 if consignee.street2 else "",
            ),
            "clientcountry": SENDING_COUNTRY_CODES[consignee.country_id.code],
            "clientzip": consignee.zip,
            "clientcity": consignee.city,
            "clientcontact": consignee.name,
            "clientphone": consignee.phone,
            "note": picking.origin,
            "weight": int(picking.shipping_weight),
            "ref": picking.name,
            "number_of_packages": picking.number_of_packages,
            "service": self.sending_service,
        }

    def sending_send_shipping(self, pickings):
        return [self.sending_create_shipping(p) for p in pickings]

    def sending_create_shipping(self, picking):
        """Send the package to Sending
        """
        sending_request = self._sending_request()
        vals = self._prepare_sending_shipping(picking)
        try:
            res = sending_request.send_shipping(vals)
            self._sending_check_error(res)
        except Exception as e:
            raise (e)
        picking.carrier_tracking_ref = res[len(res) - 12 :] if res else False
        # Create label from response
        picking.sending_get_label()
        # Return
        return {"exact_price": 0, "tracking_number": picking.carrier_tracking_ref}

    def sending_get_label(self, reference):
        """Generate label for picking
        :param picking - stock.picking record
        :returns pdf file
        """
        self.ensure_one()
        if not reference:
            return False
        sending_request = self._sending_request()
        method = "_shipping_label_%s" % self.sending_file_format.lower()
        if hasattr(sending_request, method):
            try:
                res = getattr(sending_request, method)(reference)
            except Exception as e:
                raise (e)
            return res

    def sending_cancel_shipment(self, pickings):
        """Cancel the expedition"""
        sending_request = self._sending_request()
        for picking in pickings.filtered("carrier_tracking_ref"):
            try:
                response = sending_request._cancel_shipment(
                    picking.carrier_tracking_ref
                )
                self._sending_check_error(response)
            except Exception as e:
                raise (e)
            picking.message_post(
                body=_("Sending Expedition with reference %s cancelled")
                % picking.carrier_tracking_ref
            )

    def sending_rate_shipment(self, order):
        """There's no public API so another price method should be used"""
        raise NotImplementedError(
            _(
                """
            SENDING API doesn't provide methods to compute delivery rates, so
            you should relay on another price method instead or override this
            one in your custom code.
        """
            )
        )
