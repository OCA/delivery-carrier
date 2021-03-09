# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from contextlib import contextmanager
from unittest.mock import patch

from odoo.exceptions import UserError

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case


class DeliveryCarrierLabelUpsCase(carrier_label_case.CarrierLabelCase):
    def _create_order_picking(self):
        self.env["carrier.account"].create(
            {
                "name": "UPS account",
                "delivery_type": "ups",
                "account": "username",
                "password": "password",
                "ups_access_license": "access license",
                "ups_shipper_number": "shipper number",
            }
        )
        with self._setup_mock_requests() as mock_requests:
            super()._create_order_picking()
            self.assertTrue(
                mock_requests.post.call_args[1]["json"]["ShipmentRequest"]["Shipment"][
                    "Package"
                ],
                "No products were sent",
            )

    @contextmanager
    def _setup_mock_requests(self):
        with patch(
            "odoo.addons.delivery_carrier_label_ups.models.stock_picking.requests"
        ) as mock_requests:
            mock_requests.post.return_value.json.return_value = dict(
                ShipmentResponse=dict(
                    ShipmentResults=dict(
                        ShipmentCharges=dict(
                            TotalCharges=dict(MonetaryValue=42, CurrencyCode="USD",),
                        ),
                        ShipmentIdentificationNumber="shipping_tracking",
                        PackageResults=dict(TrackingNumber="package_tracking",),
                    ),
                ),
            )
            yield mock_requests

    def _picking_data(self):
        return {
            "option_ids": [
                (
                    4,
                    self.env["delivery.carrier.option"]
                    .create(
                        {
                            "tmpl_option_id": self.env.ref(
                                "delivery_carrier_label_ups.shipping_service_code_11"
                            ).id,
                        }
                    )
                    .id,
                ),
            ]
        }

    def _get_carrier(self):
        return self.env.ref("delivery_carrier_label_ups.carrier_ups")


class TestDeliveryCarrierLabelUps(
        DeliveryCarrierLabelUpsCase,
        carrier_label_case.TestCarrierLabel):
    def test_cancel_shipment(self):
        self.assertTrue(self.picking.carrier_tracking_ref)
        with patch(
            "odoo.addons.delivery_carrier_label_ups.models.stock_picking.requests"
        ) as mock_requests:
            mock_requests.delete.return_value.json.return_value = dict(
                response=dict(errors=[dict(code=42, message="error")])
            )
            with self.assertRaises(UserError):
                self.picking.carrier_id.cancel_shipment(self.picking)
            mock_requests.delete.return_value.json.return_value = dict(response=dict())
            self.picking.cancel_shipment()
            self.assertFalse(self.picking.carrier_tracking_ref)

    def test_labels(self):
        with patch(
            "odoo.addons.delivery_carrier_label_ups.models.stock_picking.requests"
        ) as mock_requests:
            mock_requests.post.return_value.json.return_value = dict(
                LabelRecoveryResponse=dict(
                    LabelResults=dict(
                        LabelImage=dict(
                            GraphicImage=base64.b64encode(bytes("hello", "utf8")),
                            LabelImageFormat=dict(Code="PDF",),
                        ),
                        TrackingNumber="package_tracking",
                    ),
                ),
            )
            return super().test_labels()

    def test_return(self):
        shipping_data = self.picking._ups_shipping_data()['ShipmentRequest']
        action = self.env['stock.return.picking'].with_context(
            active_id=self.picking.id
        ).create({}).create_returns()
        return_picking = self.env[action['res_model']].browse(action['res_id'])
        return_data = return_picking._ups_shipping_data()['ShipmentRequest']
        self.assertEqual(
            shipping_data['Shipment']['ShipFrom']['Name'],
            return_data['Shipment']['ShipTo']['Name'],
        )
        self.assertEqual(
            shipping_data['Shipment']['ShipTo']['Name'],
            return_data['Shipment']['ShipFrom']['Name'],
        )
        ref = 'a reference'
        self.picking.carrier_tracking_ref = ref
        self.assertEqual(
            self.picking._ups_send()[0]['tracking_number'], ref,
        )
        return_picking.carrier_id = self._get_carrier()
        self.assertTrue(return_picking.show_label_button)
