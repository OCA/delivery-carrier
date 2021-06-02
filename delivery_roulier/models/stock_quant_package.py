#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..decorator import implemented_by_carrier

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import CarrierError, InvalidApiInput
except ImportError:
    _logger.debug("Cannot `import roulier`.")


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")

    # helper : move it to base ?
    def get_operations(self):
        """Get operations of the package.

        Usefull for having products and quantities
        """
        self.ensure_one()
        return self.env["stock.move.line"].search(
            [
                ("product_id", "!=", False),
                "|",
                ("package_id", "=", self.id),
                ("result_package_id", "=", self.id),
            ]
        )

    # API
    # Each method in this class have at least picking arg to directly
    # deal with stock.picking if required by your carrier use case
    @implemented_by_carrier
    def _before_call(self, picking, payload):
        pass

    @implemented_by_carrier
    def _after_call(self, picking, response):
        pass

    @implemented_by_carrier
    def _get_parcel(self, picking):
        pass

    @implemented_by_carrier
    def _carrier_error_handling(self, payload, response):
        pass

    @implemented_by_carrier
    def _invalid_api_input_handling(self, payload, response):
        pass

    @implemented_by_carrier
    def _prepare_attachments(self, picking, response):
        pass

    @implemented_by_carrier
    def _handle_attachments(self, label, response):
        pass

    @implemented_by_carrier
    def _get_tracking_link(self):
        pass

    @implemented_by_carrier
    def _generate_labels(self, picking):
        pass

    @implemented_by_carrier
    def _get_parcels(self, picking):
        pass

    @implemented_by_carrier
    def _parse_response(self, picking, response):
        pass

    # end of API

    # Core functions
    def _roulier_generate_labels(self, picking):
        # send all packs to roulier. It will decide if it makes one call per pack or
        # one call for all pack depending on the carrier.
        response = self._call_roulier_api(picking)
        self._handle_attachments(picking, response)
        return self._parse_response(picking, response)

    def _roulier_parse_response(self, picking, response):
        res = {
            # price is not managed in roulier...not yet at least
            "exact_price": 0.0,
        }
        parcels_data = []
        parcels = response.get("parcels")
        tracking_refs = []
        for parcel in parcels:
            tracking_number = parcel.get("tracking", {}).get("number")
            if tracking_number:
                tracking_refs.append(tracking_number)
            # expected format by base_delivery_carrier_label module
            label = parcel.get("label")
            # find for which package the label is. tracking number will be updated on
            # this pack later on (in base_delivery_carrier_label)
            package_id = False
            if len(self) == 1:
                package_id = self.id
            else:
                pack = self.filtered(lambda p: p.name == parcel.get("reference"))
                if len(pack) == 1:
                    package_id = pack.id

            parcels_data.append(
                {
                    "tracking_number": tracking_number,
                    "package_id": package_id,
                    "file": label.get("data"),
                    "name": "%s.%s"
                    % (
                        parcel.get("reference") or tracking_number or label.get("name"),
                        label.get("type", "").lower(),
                    ),
                    "file_type": label.get("type"),
                }
            )
        res["tracking_number"] = ";".join(tracking_refs)
        res["labels"] = parcels_data
        return res

    def _roulier_get_parcels(self, picking):
        return [pack._get_parcel(picking) for pack in self]

    def open_website_url(self):
        """Open website for parcel tracking.

        Each carrier should implement _get_tracking_link
        There is low chance you need to override this method.
        returns:
            action
        """
        self.ensure_one()
        url = self._get_tracking_link()
        client_action = {
            "type": "ir.actions.act_url",
            "name": "Shipment Tracking Page",
            "target": "new",
            "url": url,
        }
        return client_action

    def _call_roulier_api(self, picking):
        """Create a label for a given package_id (self)."""
        # There is low chance you need to override it.
        # Don't forget to implement _a-carrier_before_call
        # and _a-carrier_after_call
        account = picking._get_account(self)
        self.write({"carrier_id": picking.carrier_id.id})

        payload = {}

        payload["auth"] = picking._get_auth(account, package=self)

        payload["from_address"] = picking._get_from_address(package=self)
        payload["to_address"] = picking._get_to_address(package=self)

        payload["service"] = picking._get_service(account, package=self)
        payload["parcels"] = self._get_parcels(picking)

        # hook to override request / payload
        payload = self._before_call(picking, payload)
        try:
            # api call
            ret = roulier.get(picking.delivery_type, "get_label", payload)
        except InvalidApiInput as e:
            raise UserError(self._invalid_api_input_handling(payload, e))
        except CarrierError as e:
            raise UserError(self._carrier_error_handling(payload, e))

        # give result to someone else
        return self._after_call(picking, ret)

    # default implementations
    def _roulier_get_parcel(self, picking):
        self.ensure_one()
        weight = self.shipping_weight or self.weight
        parcel = {"weight": weight, "reference": self.name}
        return parcel

    def _roulier_before_call(self, picking, payload):
        """Add stuff to payload just before api call.

        Put here what you can't put in other methods
        (like _get_parcel, _get_service...)

        It's totally ok to do nothing here.

        returns:
            dict
        """
        return payload

    def _roulier_after_call(self, picking, response):
        """Do stuff just after api call.

        It's totally ok to do nothing here.
        """
        return response

    def _roulier_get_tracking_link(self):
        """Build a tracking url.

        You have to implement it for your carrier.
        It's like :
            'https://the-carrier.com/?track=%s' % self.parcel_tracking
        returns:
            string (url)
        """
        _logger.warning("not implemented")

    def _roulier_carrier_error_handling(self, payload, exception):
        """Build exception message for carrier error.

        It's happen when the carrier WS returns something unexpected.
        You may improve this for your carrier.
        returns:
            string
        """
        if payload.get("auth", {}).get("password"):
            payload["auth"]["password"] = "*****"
        try:
            _logger.debug(exception.response.text)
            _logger.debug(exception.response.request.body)
        except AttributeError:
            _logger.debug("No request available")
        carrier = dict(
            self.env["delivery.carrier"]._fields["delivery_type"].selection
        ).get(self.carrier_id.delivery_type)
        return _(
            "Roulier library Exception for '%s' carrier:\n"
            "\n%s\n\nSent data:\n%s" % (carrier, str(exception), payload)
        )

    def _roulier_invalid_api_input_handling(self, payload, exception):
        """Build exception message for bad input.

        It's happend when your data is not valid, like a missing value
        in the payload.

        You may improve this for your carrier.
        returns:
            string
        """
        return _("Bad input: %s\n" % str(exception))

    # There is low chance you need to override the following methods.
    def _roulier_handle_attachments(self, picking, response):
        attachments = [
            self.env["ir.attachment"].create(attachment)
            for attachment in self[0]._roulier_prepare_attachments(picking, response)
        ]  # do it once for all
        return attachments

    def _roulier_prepare_attachments(self, picking, response):
        """Prepare a list of dicts for building ir.attachments.
        Attachements are annexes like customs declarations, summary
        etc.
        returns:
            list
        """
        self.ensure_one()
        attachments = response.get("annexes")
        return [
            {
                "res_id": picking.id,
                "res_model": "stock.picking",
                "datas": attachment["data"],
                "type": "binary",
                "name": "%s-%s.%s"
                % (self.name, attachment["name"], attachment["type"]),
            }
            for attachment in attachments
        ]
