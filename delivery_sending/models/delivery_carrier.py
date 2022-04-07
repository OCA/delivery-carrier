# Copyright 2022 Impulso Diagonal - Javier Colmeiro
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
        picking.partner_id.commercial_partner_id
        if consignee.country_id.code not in SENDING_COUNTRY_CODES.keys():
            raise UserError(_("Delivery country not implemented with this carrier!"))
        return {
            "date": fields.Date.today().strftime("%d/%m/%Y"),
            "uidcustomername": sender_partner.name,
            "uidcustomeraddress": sender_partner.street,
            "uidcustomercountry": SENDING_COUNTRY_CODES[sender_partner.country_id.code],
            "uidcustomerzip": sender_partner.zip,
            "uidcustomercity": sender_partner.city,
            "clientname": consignee.name,
            "clientaddress": consignee.street,
            "clientcountry": SENDING_COUNTRY_CODES[consignee.country_id.code],
            "clientzip": consignee.zip,
            "clientcity": consignee.city,
            "clientcontact": consignee.name,
            "clientphone": consignee.phone,
            "note": picking.origin,
            "weight": int(picking.weight),
            "ref": picking.name,
            "number_of_packages": picking.number_of_packages,
            "service": self.sending_service,
        }

    def sending_send_shipping(self, pickings):
        """Send the package to Sending
        """
        sending_request = SendingRequest(self.sending_user, self.sending_access_key)
        result = []
        for picking in pickings:
            vals = self._prepare_sending_shipping(picking)
            vals.update({"tracking_number": False, "exact_price": 0})
            response = sending_request._send_shipping(vals)
            print(response)
            if not response:
                result.append(vals)
                continue
            vals["tracking_number"] = response[len(response) - 12 :]
            result.append(vals)
        return result

    def sending_get_label(self, reference):
        """Generate label for picking
        :param picking - stock.picking record
        :returns pdf file
        """
        self.ensure_one()
        if not reference:
            return False
        sending_request = SendingRequest(self.sending_user, self.sending_access_key)
        label = sending_request._shipping_label_zpl(reference)
        if not label:
            return False
        return label

    def sending_cancel_shipment(self, pickings):
        """Cancel the expedition"""
        sending_request = SendingRequest(self.sending_user, self.sending_access_key)
        for picking in pickings.filtered("carrier_tracking_ref"):
            response = sending_request._cancel_shipment(picking.carrier_tracking_ref)
            if not response:
                msg = _("Sending Cancellation failed with reason: %s" % response)
                picking.message_post(body=msg)
                continue
            picking.message_post(
                body=_("Sending Expedition with reference %s cancelled")
                % picking.carrier_tracking_ref
            )
