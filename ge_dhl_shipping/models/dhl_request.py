import logging

import requests

from odoo.addons.ge_dhl_base.models.dhl_request import DhlRequest as DhlRequestBase

_logger = logging.getLogger(__name__)


class DhlRequest(DhlRequestBase):
    def __init__(self, carrier, record, api="dhl_shipping"):
        super(DhlRequest, self).__init__(carrier, record, api=api)

    def dhl_parcel_de_provider_create_shipment(
        self, request_type, api_url, request_data, header
    ):
        _logger.info("Shipment Request API URL:::: %s" % api_url)
        _logger.info("Shipment Request Data:::: %s" % request_data)
        response_data = requests.request(
            method=request_type, url=api_url, headers=header, data=request_data
        )

        if response_data.status_code in [200]:
            response_data = response_data.json()
            _logger.info(">>> Response Data {}".format(response_data))
            return True, response_data
        else:
            return False, response_data.text
