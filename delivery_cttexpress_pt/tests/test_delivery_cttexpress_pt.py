# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase


class TestDeliveryCTTExpressPT(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client_patcher = mock.patch(
            "odoo.addons.delivery_cttexpress_pt.models.cttexpress_pt_request.Client",
            autospec=True,
        )
        cls.mock_client_class = cls.client_patcher.start()
        cls.mock_client = cls.mock_client_class.return_value
        cls.serialize_patcher = mock.patch(
            "odoo.addons.delivery_cttexpress_pt.models."
            "cttexpress_pt_request.serialize_object",
            side_effect=lambda x: x,
        )
        cls.serialize_patcher.start()
        cls.create_shipment_response = {
            "ErrorsList": {},
            "ShipmentData": {
                "ShipmentDataOutput": [
                    {
                        "ClientReference": "WH/OUT/00001",
                        "DocumentsList": {
                            "DocumentData": [
                                {
                                    "FileName": "label.pdf",
                                    "File": base64.b64encode(b"PDF").decode(),
                                }
                            ]
                        },
                        "FirstObject": "123456789PT",
                        "LabelList": {
                            "LabelData": [{"FileName": "label.zpl", "Label": "ZPL^XA"}]
                        },
                        "LastObject": "123456789PT",
                        "OriginalObjectID": "",
                    }
                ]
            },
            "Status": "Success",
        }
        cls.mock_client.service.CreateShipment.return_value = (
            cls.create_shipment_response
        )
        cls.mock_client.service.CreateShipmentWithoutPrint.return_value = {
            "ErrorsList": {},
            "ShipmentData": {"ShipmentDataOutput": []},
            "Status": "Success",
        }
        cls.mock_client.service.CompleteShipment.return_value = {
            "DeliveryNoteId": "DN1",
            "ErrorsList": {},
            "ShipmentData": {"ShipmentDataOutput": []},
            "Status": "Success",
        }
        cls.close_shipment_response = {
            "DocumentsList": {
                "DocumentData": [
                    {
                        "FileName": "CA1.pdf",
                        "File": base64.b64encode(b"CA1").decode(),
                    }
                ]
            },
            "ErrorsList": {},
            "Status": "Success",
        }
        cls.mock_client.service.CloseShipment.return_value = cls.close_shipment_response
        # The connection probe expects a business error proving the
        # credentials were accepted (the shipment codes do not exist).
        cls.close_probe_response = {
            "DocumentsList": {"DocumentData": []},
            "ErrorsList": {
                "ErrorData": [
                    {
                        "Code": 0,
                        "ErrorCode": "EW0070",
                        "Message": "Shipment not found or already closed.",
                    }
                ]
            },
            "Status": "Failure",
        }
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_cttexpress_pt = cls.env["delivery.carrier"].create(
            {
                "name": "CTT Express Portugal",
                "delivery_type": "cttexpress_pt",
                "product_id": cls.shipping_product.id,
                "debug_logging": True,
                "prod_environment": True,
                "cttexpress_pt_authentication_id": "AUTH-ID",
                "cttexpress_pt_client_id": "100029910",
                "cttexpress_pt_contract_id": "300328638",
                "cttexpress_pt_distribution_channel_id": 99,
                "cttexpress_pt_user_id": "USER-ID",
                "cttexpress_pt_sub_product": "EMSF057.01",
                "cttexpress_pt_export_type": "Permanent",
                "cttexpress_pt_upc_code": "Goods",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "is_storable": True, "weight": 1.0}
        )
        cls.wh_partner = cls.env["res.partner"].create(
            {
                "name": "My Portuguese WH",
                "city": "Viana do Castelo",
                "zip": "4900-000",
                "street": "Rua do Mexilho, 1",
                "country_id": cls.env.ref("base.pt").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Lisboa",
                "zip": "1000-001",
                "email": "odoo@test.com",
                "phone": "+351 21 123 4567",
                "street": "Rua Augusta, 1",
                "street2": "2nd floor",
                "country_id": cls.env.ref("base.pt").id,
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 2.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_cttexpress_pt
        cls.sale_order.action_confirm()
        cls.sale_order.warehouse_id.partner_id = cls.wh_partner
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_ids.quantity = 2
        cls.picking.number_of_packages = 1
        cls.picking.shipping_weight = 2.0

    @classmethod
    def tearDownClass(cls):
        mock.patch.stopall()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # The class-level client mock keeps call history across tests;
        # reset it so call assertions only see the current test.
        self.mock_client.reset_mock()

    def test_00_cttexpress_pt_test_connection(self):
        """The connection probe reports success for reachable endpoints"""
        self.mock_client.service.CloseShipment.return_value = self.close_probe_response
        action = self.carrier_cttexpress_pt.action_cttexpress_pt_test_connection()
        self.assertEqual(action["tag"], "display_notification")
        self.mock_client.service.CloseShipment.return_value = (
            self.close_shipment_response
        )

    def test_01_cttexpress_pt_test_connection_auth_error(self):
        """An authentication error on the probe raises a UserError"""
        self.mock_client.service.CloseShipment.return_value = {
            "ErrorsList": {
                "ErrorData": [
                    {
                        "Code": 0,
                        "ErrorCode": "EW0001",
                        "Message": "Ocorreu um erro na autenticação do cliente.",
                    }
                ]
            },
            "Status": "Failure",
        }
        with self.assertRaises(UserError):
            self.carrier_cttexpress_pt.action_cttexpress_pt_test_connection()
        self.mock_client.service.CloseShipment.return_value = (
            self.close_shipment_response
        )

    def test_02_cttexpress_pt_picking_confirm(self):
        """Validating the picking creates and closes the CTT shipment"""
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "123456789PT")
        self.mock_client.service.CreateShipment.assert_called_once()
        self.mock_client.service.CloseShipment.assert_called_once()

    def test_03_cttexpress_pt_picking_confirm_zpl(self):
        """The ZPL label type uses LabelList instead of DocumentsList"""
        self.carrier_cttexpress_pt.cttexpress_pt_label_type = "zpl"
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "123456789PT")

    def test_04_cttexpress_pt_api_error(self):
        """API errors are shown to the user with readable messages"""
        self.mock_client.service.CreateShipment.return_value = {
            "ErrorsList": {
                "ErrorData": [
                    {
                        "Code": 0,
                        "ErrorCode": "EW0070",
                        "Message": "Invalid recipient phone.",
                    }
                ]
            },
            "ShipmentData": {"ShipmentDataOutput": []},
            "Status": "Failure",
        }
        with self.assertRaisesRegex(UserError, "Invalid recipient phone"):
            self.picking.button_validate()
        self.mock_client.service.CreateShipment.return_value = (
            self.create_shipment_response
        )

    def test_05_cttexpress_pt_rate_shipment(self):
        """Rating validates addresses and reports missing data"""
        res = self.carrier_cttexpress_pt.cttexpress_pt_rate_shipment(self.sale_order)
        self.assertTrue(res["success"])
        self.assertEqual(res["price"], 0.0)
        self.partner.zip = False
        res = self.carrier_cttexpress_pt.cttexpress_pt_rate_shipment(self.sale_order)
        self.assertFalse(res["success"])
        self.assertIn("Recipient address", res["error_message"])
        self.partner.zip = "1000-001"

    def test_06_cttexpress_pt_phone_routing(self):
        """Mobile numbers go to MobilePhone, not Phone"""
        self.partner.phone = "+351 912 345 678"
        self.picking.button_validate()
        call = self.mock_client.service.CreateShipment.call_args
        shipment_ctt = call.kwargs["Input"]["DeliveryNote"]["ShipmentCTT"][
            "ShipmentCTT"
        ][0]
        receiver = shipment_ctt["ReceiverData"]
        self.assertEqual(receiver["Phone"], "")
        self.assertEqual(receiver["MobilePhone"], "+351912345678")

    def test_07_cttexpress_pt_cancel(self):
        """The API does not support cancelling shipments"""
        with self.assertRaises(UserError):
            self.carrier_cttexpress_pt.cttexpress_pt_cancel_shipment(self.picking)

    def test_08_cttexpress_pt_tracking_link(self):
        """The tracking link points to the CTT tracking page"""
        link = self.carrier_cttexpress_pt.cttexpress_pt_get_tracking_link(self.picking)
        self.assertIn("ctt.pt", link)

    def test_09_cttexpress_pt_onchange(self):
        """Choosing the delivery type defaults the price method"""
        carrier = self.env["delivery.carrier"].new({"delivery_type": "cttexpress_pt"})
        carrier._onchange_delivery_type_cttexpress_pt()
        self.assertEqual(carrier.price_method, "base_on_rule")
