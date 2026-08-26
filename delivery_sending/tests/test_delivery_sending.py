# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestDeliverySendingBase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_sc = cls.env["product.product"].create(
            {"type": "service", "name": "Shipping costs"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Sending",
                "delivery_type": "sending",
                "product_id": product_sc.id,
                "sending_user": "sending_odoo_test",
                "sending_access_key": "odoo",
                "sending_service": "01",
                "debug_logging": True,
                "prod_environment": False,
            }
        )
        cls.company = cls.env.ref("base.main_company")
        country_es = cls.env.ref("base.es")
        cls.company.write(
            {
                "country_id": country_es.id,
                "state_id": cls.env.ref("base.state_es_m").id,
                "city": "Madrid",
                "zip": "28231",
                "street": "Calle falsa 12",
                "phone": f"+{country_es.phone_code}976123456",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.company.country_id.id,
                "phone": cls.company.partner_id.phone,
                "email": "test@odoo.com",
                "street": cls.company.partner_id.street,
                "city": cls.company.partner_id.city,
                "zip": cls.company.partner_id.zip,
                "state_id": cls.company.partner_id.state_id.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "is_storable": True, "weight": 1}
        )
        cls.sale = cls._create_sale_order(cls)

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
        sale = order_form.save()
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=sale.id, default_carrier_id=self.carrier.id
            )
        ).save()
        delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale


class TestDeliverySending(TestDeliverySendingBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.move_ids.quantity = 10

    def test_order_sending_rate_shipment_error(self):
        with self.assertRaises(NotImplementedError):
            self.carrier.sending_rate_shipment(self.sale)

    @patch("odoo.addons.delivery_sending.models.sending_request.Client")
    def test_delivery_carrier_sending_integration(self, mock_client):
        mock_instance = mock_client.return_value
        mock_instance.service.entrada_expediciones.return_value = "OK000000001234"
        mock_instance.service.cancelarExpedicion.return_value = "OK"
        mock_instance.service.etiquetarExpedicionZPL.return_value = b"ZPL_LABEL"
        self.picking.action_confirm()
        self.picking.action_assign()
        # We need to send a context to avoid a bug with the api because there is no
        # test user.
        # We simulate the complete flow to test all carrier methods.
        self.picking.with_context(skip_errors=True).send_to_shipper()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.tracking_state_history)
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.picking.with_context(skip_errors=True).cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")

    @patch("odoo.addons.delivery_sending.models.sending_request.Client")
    def test_sending_check_error(self, mock_client):
        # Mocks send_shipping to return an error string (e.g. "ERR01")
        mock_instance = mock_client.return_value
        mock_instance.service.entrada_expediciones.return_value = "ERR01 Error message"
        self.picking.action_confirm()
        self.picking.action_assign()
        with self.assertRaisesRegex(UserError, "Sending returned an error"):
            self.picking.send_to_shipper()

    def test_prepare_sending_shipping_country_error(self):
        # Creates a partner with a country code not supported
        country_us = self.env.ref("base.us")
        self.partner.country_id = country_us
        self.picking.action_confirm()
        self.picking.action_assign()
        with self.assertRaisesRegex(
            UserError, "Delivery country not implemented with this carrier!"
        ):
            self.picking.send_to_shipper()

    @patch("odoo.addons.delivery_sending.models.sending_request.Client")
    def test_sending_create_shipping_exception(self, mock_client):
        # Mocks send_shipping to raise a generic Exception
        mock_instance = mock_client.return_value
        mock_instance.service.entrada_expediciones.side_effect = Exception("Soap Error")
        self.picking.action_confirm()
        self.picking.action_assign()
        with self.assertRaisesRegex(Exception, "Soap Error"):
            self.picking.send_to_shipper()

    def test_sending_get_label_no_reference(self):
        # Calls carrier.sending_get_label(False) and verifies it returns False
        res = self.carrier.sending_get_label(False)
        self.assertFalse(res)

    @patch("odoo.addons.delivery_sending.models.sending_request.Client")
    def test_sending_get_label_pdf(self, mock_client):
        # Sets sending_file_format to 'PDF'
        self.carrier.sending_file_format = "PDF"
        mock_instance = mock_client.return_value
        mock_instance.service.entrada_expediciones.return_value = "OK000000001234"
        mock_instance.service.etiquetarExpedicionPDF.return_value = b"PDF_LABEL"
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "000000001234")

    @patch("odoo.addons.delivery_sending.models.sending_request.Client")
    def test_sending_get_label_exception(self, mock_client):
        # Mocks the label service to raise an Exception
        mock_instance = mock_client.return_value
        mock_instance.service.etiquetarExpedicionZPL.side_effect = Exception(
            "Label Error"
        )
        with self.assertRaisesRegex(Exception, "Label Error"):
            self.carrier.sending_get_label("12345")

    @patch("odoo.addons.delivery_sending.models.sending_request.Client")
    def test_sending_cancel_shipment_exception(self, mock_client):
        # Mocks _cancel_shipment to raise an Exception
        mock_instance = mock_client.return_value
        mock_instance.service.cancelarExpedicion.side_effect = Exception("Cancel Error")
        # We need a tracking ref to enter the loop
        self.picking.carrier_tracking_ref = "12345"
        with self.assertRaisesRegex(Exception, "Cancel Error"):
            self.picking.cancel_shipment()

    def test_stock_picking_sending_get_label_no_data(self):
        # Calls picking.sending_get_label() when delivery_type is not "sending"
        self.picking.carrier_id.delivery_type = "fixed"
        res = self.picking.sending_get_label()
        self.assertIsNone(res)
        # Calls when carrier_tracking_ref is empty
        self.picking.carrier_id.delivery_type = "sending"
        self.picking.carrier_tracking_ref = False
        res = self.picking.sending_get_label()
        self.assertIsNone(res)
