# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
from unittest import mock

from odoo.tests import Form, common

request_model = (
    "odoo.addons.delivery_correos_express.models."
    "correos_express_request.CorreosExpressRequest"
)

# There is also no public test user so we mock all API requests


class TestCorreosExpressParcel(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_correos_express = cls.env["delivery.carrier"].create(
            {
                "name": "Correos Express",
                "delivery_type": "correos_express",
                "product_id": cls.shipping_product.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "consu", "is_storable": True, "name": "Test product"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Odoo Ville",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
                "email": "test@test.com",
                "street2": "Calle de La Rua, 4",
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_correos_express.id
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids[0]
        cls.picking.move_ids.quantity = 20

    @mock.patch(
        f"{request_model}.create_shipment",
        return_value={
            "codigoRetorno": 0,
            "mensajeRetorno": "",
            "datosResultado": "0870002260",
        },
    )
    def test_01_correos_express_picking_confirm_success(self, redirect_mock, *args):
        self.picking.name = f"ODOO-TEST-{time.time()}"
        self.picking.button_validate()
        self.assertEqual(
            self.picking.carrier_tracking_ref,
            "0870002260",
            "Tracking doesn't match test data",
        )

    @mock.patch(
        f"{request_model}.track_shipment",
        return_value={
            "estadoEnvios": [
                {
                    "codEstado": "1",
                    "descEstado": "not received",
                    "horaEstado": "100240",
                    "fechaEstado": "09022021",
                }
            ]
        },
    )
    def test_02_correos_express_picking_update(self, redirect_mock, *args):
        self.picking.tracking_state_update()
        self.assertEqual(
            self.picking.tracking_state_history,
            "10:02:40 09/02/2021 - [1] not received",
            "History doesn't match test data",
        )
        self.assertEqual(
            self.picking.tracking_state,
            "[1] not received",
            "State doesn't match test data",
        )

    def test_03_correos_express_get_tracking_link(self):
        tracking = self.carrier_correos_express.get_tracking_link(self.picking)
        self.assertTrue(tracking)

    @mock.patch(
        f"{request_model}.print_shipment",
        return_value=["JVBERiasdasdsdcfnsdhfbasdf=="],
    )
    def test_04_correos_express_get_label(self, redirect_mock, *args):
        label = self.picking.correos_express_get_label()
        self.assertTrue(label)

    def test_05_correos_express_rate_shipment(self):
        msg = self.carrier_correos_express.correos_express_rate_shipment(
            order=self.env["sale.order"]
        )
        self.assertIsInstance(msg, dict)

    def test_06_correos_express_no_carrier(self):
        result = self.carrier_correos_express.correos_express_get_label(None)
        self.assertFalse(result)

    def test_correos_express_tracking_state_update_no_tracking_ref(self):
        self.picking.carrier_tracking_ref = False
        result = self.carrier_correos_express.correos_express_tracking_state_update(
            self.picking
        )
        self.assertFalse(result)
