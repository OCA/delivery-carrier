# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import Mock, patch

import zeep

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case


class DeliveryCarrierLabelPaazlCase(carrier_label_case.CarrierLabelCase):
    def _create_order_picking(self):
        self.env["carrier.account"].create(
            {
                "name": "Paazl account",
                "delivery_type": "paazl",
                "account": "webshop id",
                "password": "integration password",
            }
        )
        with patch.object(zeep, "Client") as mock_client_class:
            mock_client = Mock()
            mock_client.service.order.return_value = Mock(error=False)
            mock_client.service.commitOrder.return_value = Mock(error=False)
            mock_client.service.generateLabels.return_value = Mock(
                error=False,
                labels=b"hello world",
                metaData=[{"trackingNumber": "number"}],
            )
            mock_client_class.return_value = mock_client
            super()._create_order_picking()

    def _get_carrier(self):
        return self.env.ref("delivery_carrier_label_paazl.carrier_paazl")
