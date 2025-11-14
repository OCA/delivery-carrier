import logging
from base64 import b64encode

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

try:
    from roulier import roulier
    from roulier.exception import InvalidApiInput  # CarrierError
except ImportError:
    _logger.debug("Cannot `import roulier`.")


class DepositSlip(models.Model):
    _inherit = "deposit.slip"

    def _geodis_prepare_data(self):
        """Create lines for each picking.

        In a EDI file order is important.
        Returns a dict per agencies

        @returns []
        """
        self.ensure_one()

        # build a dict of pickings per agencies
        def pickings_agencies(pickings):
            agencies = {}
            for picking in pickings:
                agency = picking._get_carrier_agency()
                agencies.setdefault(agency, {"senders": None, "pickings": []},)[
                    "pickings"
                ].append(picking)
            return agencies

        pickagencies = pickings_agencies(self.picking_ids)

        # build a dict of pickings per sender
        def pickings_senders(pickings):
            senders = {}
            for picking in pickings:
                partner = picking._get_sender(None)
                senders.setdefault(
                    partner.id,
                    {"pickings": [], "account": picking._get_account()},
                )["pickings"].append(picking)
            return senders

        for _agency, pickagency in pickagencies.items():
            pickagency["senders"] = pickings_senders(pickagency["pickings"])

        # build a response file per agency / sender
        files = []
        i = 0
        for agency, pickagency in pickagencies.items():
            for sender_id, picksender in pickagency["senders"].items():
                i += 1

                # consolidate pickings for agency / sender
                shipments = [
                    picking._geodis_fr_prepare_edi()
                    for picking in picksender["pickings"]
                ]
                # we need one of the pickings to lookup addresses
                picking = picksender["pickings"][0]
                from_address = self._geodis_get_from_address(picking)
                agency_address = self._geodis_get_agency_address(picking, agency)
                account = picksender["account"]

                service = {
                    "depositId": "%s%s" % (self.id, i),
                    "depositDate": self.create_date,
                    "customerId": account.geodis_fr_customer_id,
                    "interchangeSender": agency.geodis_fr_interchange_sender,
                    "interchangeRecipient": agency.geodis_fr_interchange_recipient,
                }
                files.append(
                    {
                        "shipments": shipments,
                        "from_address": from_address,
                        "agency_address": agency_address,
                        "service": service,
                        "agency_id": agency.external_reference,
                        "sender_id": sender_id,
                    }
                )
        return files

    def _geodis_get_from_address(self, picking):
        """Return a dict of the sender."""
        partner = picking._get_sender(None)
        address = picking._convert_address(partner)
        address["siret"] = partner.siret or ""
        return address

    def _geodis_get_agency_address(self, picking, agency):
        """Return a dict the agency."""
        partner = agency.partner_id
        address = picking._convert_address(partner)
        address["siret"] = partner.siret or ""
        return address

    def _geodis_create_edi_file(self, payload):
        """Create a edi file with headers and data.

        One agency per call.

        params:
            payload : roulier.get_api("edi")
        return: string
        """
        try:
            edi = roulier.get(self.delivery_type, "get_edi", payload)
        except InvalidApiInput as e:
            raise UserError(_("Bad input: %s\n") % str(e)) from e
        return edi

    def _get_geodis_attachment_name(self, idx, payload_agency):
        return "%s_%s.txt" % (self.name, idx)

    def _geodis_create_attachments(self):
        """Create EDI files in attachment."""
        payloads = self._geodis_prepare_data()
        attachments = self.env["ir.attachment"]
        for idx, payload_agency in enumerate(payloads, start=1):
            edi_file = self._geodis_create_edi_file(payload_agency)
            file_name = self._get_geodis_attachment_name(idx, payload_agency)
            vals = {
                "name": file_name,
                "res_id": self.id,
                "res_model": "deposit.slip",
                "datas": b64encode(edi_file.encode("utf8")),
                "type": "binary",
            }
            attachments += self.env["ir.attachment"].create(vals)
        return attachments

    def create_edi_file(self):
        self.ensure_one()
        if self.delivery_type == "geodis_fr":
            return self._geodis_create_attachments()
        else:
            return super().create_edi_file()
