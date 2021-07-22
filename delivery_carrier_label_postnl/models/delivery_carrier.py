# Copyright 2021 George Daramouskas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime
from odoo import models, fields, exceptions
from postnl_service_shipment.configuration import Configuration
from postnl_service_shipment import ApiClient, DefaultApi
from postnl_service_shipment.rest import ApiException
from postnl_service_shipment.models.request import Request
from postnl_service_shipment.models.request_customer import RequestCustomer
from postnl_service_shipment.models.request_customer_address import \
    RequestCustomerAddress
from postnl_service_shipment.models.request_message import RequestMessage
from postnl_service_shipment.models.request_shipments import RequestShipments
from postnl_service_shipment.models.request_addresses import RequestAddresses
from postnl_service_shipment.models.request_dimension import RequestDimension


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("postnl", "PostNL")])

    def postnl_send_shipping(self, pickings):
        res = []
        client = self._postnl_get_client()
        apikey = client.api_client.configuration.get_api_key_with_prefix(
            "apikey",
        )
        for picking in pickings:
            try:
                body = self._postnl_get_send_shipping_body(picking)
                response = client.shipment_v22_label_post(body, apikey)
                # we will only care about the first shipment since we do not
                # support multiple shipments yet
                shipment = response.response_shipments[0]
                label = shipment.labels[0]
                res.append(
                    {
                        "exact_price": -1,
                        "tracking_number": shipment.barcode,
                        "labels": [{
                            "name": shipment.barcode,
                            "file": label.content,
                            "file_type": label.output_type,
                        }],
                    },
                )
                picking.write({"carrier_tracking_ref": shipment.barcode})
            except ApiException as e:
                raise exceptions.UserError(e)
        return res

    def postnl_get_tracking_link(self, picking):
        apiurl = self.env["ir_config.parameter"].get_param(
            "delivery_carrier_label_postnl.url_shipping_service",
        )
        return apiurl + "/v2/status/barcode/{}".format(
            picking.carrier_tracking_ref,
        )

    def _postnl_get_send_shipping_body(self, picking):
        request = Request(
            # the senders data (ours)
            customer=RequestCustomer(
                address=RequestCustomerAddress(
                    city=picking.company_id.city,
                    company_name=picking.company_id.name,
                    countrycode=picking.company_id.country_id.code,
                    street=picking.company_id.street,
                    zipcode=picking.company_id.zip,
                    region=picking.company_id.state_id.name,
                ),
                collection_location=None,
                contact_person=None,
                customer_code=None,
                customer_number=None,
                email=None,
                name=None,
            ),
            message=RequestMessage(
                message_id=None,
                message_time_stamp=datetime.now().strftime(
                    "%d-%m-%Y %H:%M:%S",
                ),
            ),
            shipments=[
                RequestShipments(
                    # the receivers data
                    addresses=[RequestAddresses(
                        address_type="01",
                        city=picking.partner_id.city,
                        countrycode=picking.partner_id.country_id.code,
                        company_name=None,
                        name=picking.partner_id.name,
                        street=picking.partner_id.street,
                        house_nr=picking.partner_id.street_number,
                        zipcode=picking.partner_id.zip,
                        region=picking.partner_id.state_id.name,
                        fist_name=None,
                    )],
                    barcode=None,
                    delivery_address=None,
                    product_code_delivery=None,
                    dimension=RequestDimension(
                        weight=picking.shipping_weight,
                        volume=picking.volume,
                    ),
                ),
            ])
        return request

    def _postnl_get_client(self):
        ir_config_parameter = self.env["ir.config_parameter"]
        apikey = ir_config_parameter.get_param(
            "delivery_carrier_label_postnl.apikey",
        )
        apiurl = ir_config_parameter.get_param(
            "delivery_carrier_label_postnl.url_shipping_service",
        )
        configuration = Configuration()
        configuration.host = apiurl
        configuration.api_key = {"apikey": apikey}
        return DefaultApi(ApiClient(configuration))
