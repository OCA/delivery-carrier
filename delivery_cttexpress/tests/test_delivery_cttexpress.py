# Copyright 2022 Tecnativa - David Vidal
# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import datetime
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase

from odoo.addons.delivery_cttexpress.models.delivery_carrier import DeliveryCarrier


class MockZeepObj:
    """Helper to mock Zeep response objects"""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestDeliveryCTTExpress(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.zeep_patcher = mock.patch(
            "odoo.addons.delivery_cttexpress.models.cttexpress_request.Client",
            autospec=True,
        )
        cls.mock_client_class = cls.zeep_patcher.start()
        cls.mock_client = cls.mock_client_class.return_value
        cls.serialize_patcher = mock.patch(
            "odoo.addons.delivery_cttexpress.models.cttexpress_request.serialize_object",
            side_effect=lambda x: x,
        )
        cls.serialize_patcher.start()
        cls.log_patcher = mock.patch.object(
            DeliveryCarrier,
            "_ctt_log_request",
            autospec=True,
            return_value=None,
        )
        cls.log_patcher.start()
        cls.mock_client.service.ValidateUser.return_value = [
            MockZeepObj(ErrorCode=0, ErrorMessage="OK")
        ]
        cls.mock_client.service.GetServiceTypes.return_value = MockZeepObj(
            ErrorCodes=None,
            Services=MockZeepObj(
                ClientShippingType=[
                    MockZeepObj(ShippingTypeCode="19H", ShippingTypeDescription="19H")
                ]
            ),
        )
        cls.mock_client.service.ManifestShipping.return_value = MockZeepObj(
            ErrorCodes=None,
            Documents=MockZeepObj(
                Document=[MockZeepObj(FileName="label.pdf", FileContent=b"PDF")]
            ),
            ShippingCode="123456789",
        )
        cls.mock_client.service.GetTracking.return_value = MockZeepObj(
            ErrorCodes=None,
            Tracking=MockZeepObj(
                Tracking=[
                    {
                        "StatusCode": "1",
                        "StatusDescription": "RECIBIDA",
                        "IncidentCode": "",
                        "IncidentDescription": "",
                        "StatusDateTime": datetime(2022, 1, 1, 10, 0, 0),
                    }
                ]
            ),
        )
        cls.mock_client.service.GetDocumentsV2.return_value = MockZeepObj(
            ErrorCodes=None,
            Documents=MockZeepObj(
                Document=[MockZeepObj(FileName="doc.pdf", FileContent=b"DOC")]
            ),
        )
        cls.mock_client.service.ReportShipping.return_value = MockZeepObj(
            ErrorCodes=None,
            Documents=MockZeepObj(
                Document=[MockZeepObj(FileName="report.xlsx", FileContent=b"XLSX")]
            ),
        )
        cls.mock_client.service.CreateRequest.return_value = MockZeepObj(
            ErrorCodes=None, RequestShippingCode="REQ987"
        )
        cls.mock_client.service.CancelShipping.return_value = [
            MockZeepObj(ErrorCode=0, ErrorMessage="OK")
        ]
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_cttexpress = cls.env["delivery.carrier"].create(
            {
                "name": "CTT Express",
                "delivery_type": "cttexpress",
                "product_id": cls.shipping_product.id,
                "debug_logging": True,
                "prod_environment": True,
                "cttexpress_user": "ODOO1",
                "cttexpress_password": "PASSWORD",
                "cttexpress_agency": "000002",
                "cttexpress_contract": "1",
                "cttexpress_customer": "ODOO1",
                "cttexpress_shipping_type": "19H",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "consu", "name": "Test product", "weight": 0.525}
        )
        cls.wh_partner = cls.env["res.partner"].create(
            {
                "name": "My Spanish WH",
                "city": "Zaragoza",
                "zip": "50001",
                "street": "C/ Mayor, 1",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Madrid",
                "zip": "28001",
                "email": "odoo@test.com",
                "street": "Calle de La Rua, 3",
                "street2": "Floor 2",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_cttexpress
        cls.sale_order.action_confirm()
        # Ensure shipper address
        cls.sale_order.warehouse_id.partner_id = cls.wh_partner
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_ids.quantity = 20

    @classmethod
    def tearDownClass(cls):
        cls.log_patcher.stop()
        cls.serialize_patcher.stop()
        cls.zeep_patcher.stop()
        super().tearDownClass()

    def test_00_cttexpress_test_connection_success(self):
        """Test successful credentials validation"""
        self.carrier_cttexpress.action_ctt_validate_user()

    def test_00_cttexpress_test_connection_fail(self):
        """Test credentials validation with error"""
        self.mock_client.service.ValidateUser.return_value = [
            MockZeepObj(ErrorCode="100", ErrorMessage="Bad Password")
        ]
        with self.assertRaises(UserError):
            self.carrier_cttexpress.action_ctt_validate_user()
        self.mock_client.service.ValidateUser.return_value = [
            MockZeepObj(ErrorCode=0, ErrorMessage="OK")
        ]

    def test_01_cttexpress_picking_confirm_simple(self):
        """The picking is confirm and the shipping is recorded to CTT Express"""
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.picking.tracking_state_update()
        self.assertTrue(self.picking.tracking_state)
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)

    def test_02_cttexpress_picking_confirm_simple_pt(self):
        """We can deliver from Portugal as well"""
        self.wh_partner.country_id = self.env.ref("base.pt")
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)

    def test_03_cttexpress_manifest(self):
        """Test Manifest Generation"""
        wizard = self.env["cttexpress.manifest.wizard"].create({})
        wizard.carrier_ids = self.carrier_cttexpress
        res = wizard.get_manifest()
        self.assertTrue(wizard.attachment_ids)
        self.assertEqual(wizard.state, "done")
        self.assertTrue(res.get("res_id"))
        wizard2 = self.env["cttexpress.manifest.wizard"].create({})
        wizard2.get_manifest()
        self.assertTrue(wizard2.attachment_ids)

    def test_04_cttexpress_pickup(self):
        """Test Pickup Request"""
        wizard = self.env["cttexpress.pickup.wizard"].create(
            {"carrier_id": self.carrier_cttexpress.id, "min_hour": 0.0}
        )
        wizard.create_pickup_request()
        self.assertTrue(wizard.code)
        self.assertEqual(wizard.state, "done")

    def test_05_cttexpress_onchanges(self):
        """Test onchanges in carrier and wizard"""
        wizard = self.env["cttexpress.pickup.wizard"].new(
            {
                "min_hour": 25.0,
                "max_hour": -1.0,
            }
        )
        wizard._onchange_hours()
        self.assertEqual(wizard.min_hour, 23.99)
        self.assertEqual(wizard.max_hour, 23.99)
        carrier = self.env["delivery.carrier"].new({"delivery_type": "cttexpress"})
        carrier._onchange_delivery_type_ctt()
        self.assertTrue(carrier.prod_environment)
        self.assertEqual(carrier.price_method, "base_on_rule")
        carrier.cttexpress_shipping_type = "48H"
        with self.assertRaises(UserError):
            carrier._onchange_cttexpress_shipping_type()
        carrier.cttexpress_shipping_type = "19H"
        carrier._onchange_cttexpress_shipping_type()

    def test_06_cttexpress_tracking_link(self):
        """Test tracking link generation"""
        self.picking.carrier_tracking_ref = "123456"
        link = self.carrier_cttexpress.cttexpress_get_tracking_link(self.picking)
        self.assertIn("123456", link)

    def test_07_cttexpress_labels(self):
        """Test label retrieval on picking and stock.picking wrapper"""
        self.picking.carrier_tracking_ref = False
        res = self.picking.cttexpress_get_label()
        self.assertFalse(res)
        self.picking.carrier_tracking_ref = "123456"
        label = self.picking.cttexpress_get_label()
        self.assertEqual(label[0][0], "doc.pdf")
        self.assertEqual(label[0][1], b"DOC")

    def test_08_cttexpress_prepare_shipping_vals(self):
        """Test the values prepared for the API"""
        vals = self.carrier_cttexpress._prepare_cttexpress_shipping(self.picking)
        self.assertIn("Floor 2", vals["RecipientAddress"])
        expected_weight = int(self.picking.shipping_weight * 1000) or 1
        self.assertEqual(vals["Weight"], expected_weight)
        self.assertEqual(vals["ItemsCount"], 1)

    def test_09_cttexpress_error_handling(self):
        """Test API errors properly raise UserError"""
        self.mock_client.service.ManifestShipping.return_value = MockZeepObj(
            ErrorCodes=MockZeepObj(
                ErrorResult=[MockZeepObj(ErrorCode="500", ErrorMessage="Internal")]
            ),
            Documents=None,
            ShippingCode="",
        )
        with self.assertRaisesRegex(UserError, "500 - Internal"):
            self.picking.button_validate()
        self.mock_client.service.ManifestShipping.return_value = MockZeepObj(
            ErrorCodes=None,
            Documents=MockZeepObj(
                Document=[MockZeepObj(FileName="l.pdf", FileContent=b"P")]
            ),
            ShippingCode="12345",
        )

    def test_10_missing_labels_during_manifest(self):
        """Sometimes picking validation doesn't return label immediately"""

        def get_documents_v2_error(*args, **kw):
            return MockZeepObj(
                ErrorCodes=MockZeepObj(
                    ErrorResult=[
                        MockZeepObj(ErrorCode="1004", ErrorMessage="Not Ready")
                    ]
                ),
                Documents=None,
            )

        self.mock_client.service.GetDocumentsV2.side_effect = get_documents_v2_error
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.mock_client.service.GetDocumentsV2.side_effect = None

    def test_11_stock_picking_wrappers(self):
        """Test stock.picking bypasses code when not cttexpress"""
        dummy_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Dummy",
                "delivery_type": "base_on_rule",
                "product_id": self.shipping_product.id,
            }
        )
        self.picking.carrier_id = dummy_carrier
        self.assertFalse(self.picking.cttexpress_get_label())

    def test_12_cttexpress_misc(self):
        mock_req = mock.Mock()
        mock_req.ctt_last_request = "some xml"
        mock_req.ctt_last_response = "some response"
        self.carrier_cttexpress._ctt_log_request(mock_req)
        tracking = {
            "StatusDateTime": datetime.now(),
            "StatusCode": "01",
            "StatusDescription": "Desc",
            "IncidentCode": "INC01",
            "IncidentDescription": "Inc Desc",
        }
        self.carrier_cttexpress._cttexpress_format_tracking(tracking)
        self.carrier_cttexpress.cttexpress_shipping_type = False
        self.carrier_cttexpress._onchange_cttexpress_shipping_type()
        self.carrier_cttexpress.cttexpress_shipping_type = "19H"
        with mock.patch.object(
            type(self.carrier_cttexpress),
            "action_ctt_validate_user",
            side_effect=UserError("Validation failed"),
        ):
            self.carrier_cttexpress._onchange_cttexpress_shipping_type()
        with mock.patch.object(
            type(self.carrier_cttexpress),
            "cttexpress_get_label",
            side_effect=UserError("Unexpected error"),
        ):
            with self.assertRaisesRegex(UserError, "Unexpected error"):
                self.carrier_cttexpress.cttexpress_send_shipping(self.picking)
        self.picking.carrier_tracking_ref = "123"
        with mock.patch(
            "odoo.addons.delivery_cttexpress.models.cttexpress_request.CTTExpressRequest.cancel_shipping",
            side_effect=Exception("Generic Error"),
        ):
            with self.assertRaisesRegex(Exception, "Generic Error"):
                self.carrier_cttexpress.cttexpress_cancel_shipment(self.picking)
        self.assertFalse(self.carrier_cttexpress.cttexpress_get_label(False))
        self.mock_client.service.GetDocumentsV2.return_value = MockZeepObj(
            ErrorCodes=None,
            Documents=None,
        )
        self.assertFalse(self.carrier_cttexpress.cttexpress_get_label("some_ref"))
