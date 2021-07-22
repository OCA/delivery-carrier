# Copyright 2021 George Daramouskas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from base64 import b64encode
from unittest.mock import patch

from postnl_service_shipment.models.response import Response
from postnl_service_shipment.models.response_response_shipments \
    import ResponseResponseShipments
from postnl_service_shipment.models.response_labels import ResponseLabels
from odoo.addons.base_delivery_carrier_label.tests.carrier_label_case \
    import CarrierLabelCase
from odoo.addons.delivery_carrier_label_postnl.models.delivery_carrier \
    import DeliveryCarrier
from odoo import exceptions


mock_response = Response(
    merged_labels=[],
    response_shipments=[
        ResponseResponseShipments(
            labels=[
                ResponseLabels(
                    content=b64encode(b"test"),
                    output_type="PDF",
                )
            ],
            barcode="123456789",
        ),
    ],
)
func = DeliveryCarrier.postnl_send_shipping


def _wrapper(self, pickings):
    return func(self, pickings)


class PostNLCase(CarrierLabelCase):

    def _get_carrier(self):
        return self.env.ref(
            "delivery_carrier_label_postnl.delivery_carrier_postnl",
        )

    @property
    def transfer_in_setup(self):
        return False

    @patch(
        "odoo.addons.delivery_carrier_label_postnl.models."
        "delivery_carrier.DefaultApi.shipment_v22_label_post",
        return_value=mock_response)
    @patch(
        "odoo.addons.delivery_carrier_label_postnl.models."
        "delivery_carrier.DeliveryCarrier.postnl_send_shipping",
        side_effect=_wrapper,
        autospec=True)
    @patch(
        "odoo.addons.base_delivery_carrier_label.models."
        "stock_picking.StockPicking.attach_shipping_label")
    def test_send_shipping(
            self,
            wrap_attach_shipping_label,
            wrap_postnl_send_shipping,
            _):
        self.picking.send_to_shipper()
        wrap_postnl_send_shipping.assert_called_with(
            self._get_carrier(),
            self.picking,
        )
        wrap_attach_shipping_label.assert_called_with(
            {
                "name": "123456789",
                "file": b64encode(b"test"),
                "file_type": "PDF",
            },
        )

    def test_bad_key(self):
        with self.assertRaises(exceptions.UserError):
            self.picking.send_to_shipper()
