# ruff: noqa: E501

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.delivery_schenker.models.stock_picking import StockPicking


class TestDeliverySchenker(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product = cls.env["product.product"].create(
            {"name": "Schenker delivery", "type": "service", "list_price": 12.0}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Schenker",
                "delivery_type": "schenker",
                "product_id": product.id,
                "schenker_access_key": "access-key",
                "schenker_group_id": "group",
                "schenker_user": "user",
                "schenker_service_land": "CON",
                "schenker_service_air": "f",
            }
        )

    def _request_patch(self):
        return patch(
            "odoo.addons.delivery_schenker.models.delivery_carrier.SchenkerRequest"
        )

    def _picking(self, tracking_ref="tracking"):
        picking = MagicMock()
        picking.carrier_tracking_ref = tracking_ref
        picking.name = "WH/OUT/0001"
        picking.shipping_weight = 4.0
        picking.weight = 5.0
        picking.number_of_packages = 1
        picking.date_done = datetime(2026, 1, 2, 12, 0, 0)
        picking.partner_id = SimpleNamespace(display_name="Customer", name="Customer")
        picking.sale_id = SimpleNamespace(incoterm=SimpleNamespace(code=False))
        picking.move_line_ids = []
        return picking

    def test_credentials_logging_and_barcode_values(self):
        self.assertEqual(
            self.carrier._get_schenker_credentials(),
            {
                "prod": False,
                "access_key": "access-key",
                "group_id": "group",
                "user": "user",
            },
        )
        request = SimpleNamespace(
            history=SimpleNamespace(
                last_sent={"envelope": etree.Element("sent")},
                last_received={"envelope": etree.Element("received")},
            )
        )
        with patch.object(type(self.carrier), "log_xml") as log_xml:
            self.carrier._schenker_log_request(request, self._picking())
        self.assertEqual(log_xml.call_count, 2)

        request.history.last_sent = None
        self.carrier._schenker_log_request(request, self._picking())

        self.carrier.schenker_barcode_mail = False
        self.carrier.schenker_barcode_format = "A6"
        self.assertEqual(
            self.carrier._prepare_schenker_barcode(), {"barcodeRequest": "A6"}
        )
        self.carrier.schenker_barcode_mail = "labels@example.com"
        self.carrier.schenker_barcode_format = "A4"
        self.assertEqual(
            self.carrier._prepare_schenker_barcode(),
            {
                "barcodeRequest": "A4",
                "barcodeRequestEmail": "labels@example.com",
                "start_pos": 1,
                "separated": False,
            },
        )

    def test_address_product_metric_and_dates(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Customer",
                "street": "Main street",
                "street2": "Second floor",
                "zip": "28001",
                "city": "Madrid",
                "email": "customer@example.com",
                "phone": "123",
                "country_id": self.env.ref("base.es").id,
            }
        )
        address = self.carrier._prepare_schenker_address(partner, "SHIPPER")
        self.assertEqual(address["type"], "SHIPPER")
        self.assertEqual(address["email"], "customer@example.com")
        self.assertEqual(address["street2"], "Second floor")
        mobile_partner = SimpleNamespace(
            name="Mobile customer",
            street="Main street",
            zip="28001",
            city="Madrid",
            state_id=SimpleNamespace(code=False, name=False),
            country_id=partner.country_id,
            lang=partner.lang,
            email=False,
            mobile="456",
            phone=False,
            street2=False,
        )
        self.assertEqual(
            self.carrier._prepare_schenker_address(mobile_partner)["mobilePhone"], "456"
        )

        picking = self._picking()
        picking.picking_type_id.warehouse_id.partner_id = partner
        picking.company_id.partner_id = self.env["res.partner"]
        picking.partner_id = partner
        addresses = self.carrier._schenker_shipping_address(picking)
        self.assertEqual(addresses[0]["type"], "SHIPPER")
        self.assertEqual(addresses[1]["type"], "CONSIGNEE")
        picking.picking_type_id.warehouse_id.partner_id = self.env["res.partner"]
        picking.company_id.partner_id = partner
        self.assertEqual(
            self.carrier._schenker_shipping_address(picking)[0]["name1"], "Customer"
        )

        for booking_type, expected in (
            ("land", "CON"),
            ("air", "f"),
            ("ocean_fcl", "fcl"),
            ("ocean_lcl", "lcl"),
        ):
            self.carrier.schenker_booking_type = booking_type
            self.assertEqual(self.carrier._schenker_shipping_product(), expected)
        self.env["ir.config_parameter"].set_param("product.weight_in_lbs", "0")
        self.assertEqual(self.carrier._schenker_metric_system(), "METRIC")
        self.env["ir.config_parameter"].set_param("product.weight_in_lbs", "1")
        self.assertEqual(self.carrier._schenker_metric_system(), "IMPERIAL")
        dates = self.carrier._schenker_pickup_dates(self._picking())
        self.assertIn("T00:00:00", dates["pickUpDateFrom"])
        self.assertIn("T23:59:59", dates["pickUpDateTo"])

    def test_shipping_information_and_preparation(self):
        package_type = SimpleNamespace(
            shipper_package_code="BOX", schenker_stackable=True
        )
        package = SimpleNamespace(
            shipping_weight=0.0,
            weight=2.0,
            volume=1.2,
            name="PACK001",
            package_type_id=package_type,
        )
        picking = self._picking()
        self.assertEqual(
            self.carrier._schenker_shipping_information_package(picking, package)[
                "grossWeight"
            ],
            2.0,
        )
        package_without_volume = SimpleNamespace(
            shipping_weight=1.0,
            weight=2.0,
            quant_ids=[
                SimpleNamespace(quantity=2, product_id=SimpleNamespace(volume=0.5))
            ],
            name="PACK002",
            package_type_id=package_type,
        )
        self.assertEqual(
            self.carrier._schenker_shipping_information_package(
                picking, package_without_volume
            )["volume"],
            1.0,
        )

        package_record = self.env["stock.package"].create({"name": "PACK003"})
        move_line = SimpleNamespace(result_package_id=package_record)
        picking.move_line_ids = [move_line]
        with patch.object(
            type(self.carrier),
            "_schenker_shipping_information_package",
            return_value={"volume": 1.2},
        ):
            self.assertEqual(
                self.carrier._schenker_shipping_information(picking), [{"volume": 1.2}]
            )

        picking.move_line_ids = [
            SimpleNamespace(
                quantity=2,
                result_package_id=False,
                product_uom_id=SimpleNamespace(
                    _compute_quantity=lambda quantity, uom: quantity
                ),
                product_id=SimpleNamespace(uom_id=object(), volume=0.5),
            )
        ]
        self.assertEqual(
            self.carrier._schenker_shipping_information(picking)[0]["volume"], 1.0
        )
        self.carrier.schenker_measure_unit = "VOLUME"
        self.assertEqual(
            self.carrier._schenker_measures(
                picking, {"shippingInformation": {"volume": 1}}
            ),
            {"measureUnitVolume": 1},
        )
        self.carrier.schenker_measure_unit = "PIECES"
        self.assertEqual(self.carrier._schenker_measures(picking, {}), {})

        self.carrier.schenker_measure_unit = "VOLUME"
        self.carrier.schenker_booking_type = "land"
        with (
            patch.object(
                type(self.carrier),
                "_prepare_schenker_barcode",
                return_value={"barcodeRequest": "A6"},
            ),
            patch.object(
                type(self.carrier),
                "_schenker_shipping_information",
                return_value=[{"volume": 1}],
            ),
            patch.object(
                type(self.carrier),
                "_schenker_shipping_address",
                return_value=[{"type": "SHIPPER"}],
            ),
            patch.object(
                type(self.carrier), "_schenker_metric_system", return_value="METRIC"
            ),
            patch.object(
                type(self.carrier),
                "_schenker_pickup_dates",
                return_value={"from": "date"},
            ),
        ):
            vals = self.carrier._prepare_schenker_shipping(self._picking())
        self.assertEqual(vals["measurementType"], "METRIC")
        self.assertEqual(vals["shippingInformation"]["volume"], 1)
        self.assertEqual(vals["measureUnitVolume"], 1)

    def test_shipping_cancellation_labels_and_tracking_link(self):
        picking = self._picking()
        with (
            self._request_patch() as request_class,
            patch.object(
                type(self.carrier),
                "_prepare_schenker_shipping",
                return_value={"payload": True},
            ),
            patch.object(type(self.carrier), "_schenker_log_request") as log_request,
        ):
            request_class.return_value._send_shipping.return_value = {
                "booking_id": "booking",
                "barcode": "pdf",
            }
            result = self.carrier.schenker_send_shipping([picking])
        self.assertEqual(result[0]["tracking_number"], "booking")
        picking.message_post.assert_called_once()
        self.assertTrue(log_request.called)

        with (
            self._request_patch() as request_class,
            patch.object(
                type(self.carrier), "_prepare_schenker_shipping", return_value={}
            ),
            patch.object(type(self.carrier), "_schenker_log_request") as log_request,
        ):
            request_class.return_value._send_shipping.side_effect = RuntimeError(
                "failure"
            )
            with self.assertRaisesRegex(RuntimeError, "failure"):
                self.carrier.schenker_send_shipping([self._picking()])
        log_request.assert_called_once()

        without_response = self._picking()
        with (
            self._request_patch() as request_class,
            patch.object(
                type(self.carrier), "_prepare_schenker_shipping", return_value={}
            ),
            patch.object(type(self.carrier), "_schenker_log_request"),
        ):
            request_class.return_value._send_shipping.return_value = False
            self.assertFalse(
                self.carrier.schenker_send_shipping([without_response])[0][
                    "tracking_number"
                ]
            )

        without_tracking = self._picking(tracking_ref=False)
        with (
            self._request_patch() as request_class,
            patch.object(type(self.carrier), "_schenker_log_request") as log_request,
        ):
            self.assertTrue(
                self.carrier.schenker_cancel_shipment([without_tracking, picking])
            )
        request_class.return_value._cancel_shipment.assert_called_once_with("tracking")
        log_request.assert_called_once()

        with (
            self._request_patch() as request_class,
            patch.object(type(self.carrier), "_schenker_log_request") as log_request,
        ):
            request_class.return_value._cancel_shipment.side_effect = RuntimeError(
                "failure"
            )
            with self.assertRaisesRegex(RuntimeError, "failure"):
                self.carrier.schenker_cancel_shipment([self._picking()])
        log_request.assert_called_once()

        self.assertFalse(self.carrier.schenker_get_label(False))
        self.carrier.schenker_barcode_format = "A6"
        with self._request_patch() as request_class:
            request_class.return_value._shipping_label.return_value = "pdf"
            self.assertEqual(self.carrier.schenker_get_label("booking"), "pdf")
        self.carrier.schenker_barcode_format = "A4"
        with self._request_patch() as request_class:
            request_class.return_value._shipping_label.return_value = False
            self.assertFalse(self.carrier.schenker_get_label("booking"))
            self.assertEqual(
                request_class.return_value._shipping_label.call_args.args[1][
                    "_value_1"
                ],
                "A4",
            )
        self.assertIn("tracking", self.carrier.schenker_get_tracking_link(picking))
        self.assertEqual(
            self.carrier._prepare_schenker_tracking(picking)["reference"], "tracking"
        )

    def test_tracking_rate_onchanges_and_picking_label(self):
        picking = self._picking(tracking_ref=False)
        self.assertIsNone(self.carrier.schenker_tracking_state_update(picking))
        event = SimpleNamespace(
            Date="2026-01-02 00:00:00",
            Time=datetime(2026, 1, 2, 10, 30, 0).time(),
            OccurredAt=SimpleNamespace(LocationName="Madrid"),
            Status="DLV",
            StatusDescription=SimpleNamespace(_value_1="Delivered"),
        )
        info = SimpleNamespace(
            LastEvent="DLV",
            StatusEventList=SimpleNamespace(StatusEvent=[event]),
        )
        picking = self._picking()
        with self._request_patch() as request_class:
            request_class.return_value._get_tracking_states.return_value = {
                "shipment": [
                    SimpleNamespace(
                        ShipmentInfo=SimpleNamespace(ShipmentBasicInfo=info)
                    )
                ]
            }
            self.carrier.schenker_tracking_state_update(picking)
        self.assertEqual(
            picking.write.call_args.args[0]["delivery_state"], "customer_delivered"
        )
        with self._request_patch() as request_class:
            request_class.return_value._get_tracking_states.return_value = {}
            self.carrier.schenker_tracking_state_update(self._picking())

        rate = self.carrier.schenker_rate_shipment(False)
        self.assertTrue(rate["success"])
        self.carrier.schenker_booking_type = "land"
        self.carrier.onchange_schenker_booking_type()
        self.carrier.schenker_booking_type = "air"
        with self.assertRaises(UserError):
            self.carrier.onchange_schenker_booking_type()
        self.carrier.schenker_measure_unit = "VOLUME"
        self.carrier.onchange_schenker_measure_unit()
        self.carrier.schenker_measure_unit = "PIECES"
        with self.assertRaises(UserError):
            self.carrier.onchange_schenker_measure_unit()

        picking_for_label = MagicMock()
        picking_for_label.env = self.env
        picking_for_label.delivery_type = "schenker"
        picking_for_label.carrier_tracking_ref = "tracking"
        picking_for_label.carrier_id.schenker_get_label.return_value = "pdf"
        self.assertEqual(StockPicking.schenker_get_label(picking_for_label), "pdf")
        picking_for_label.message_post.assert_called_once()
        picking_for_label.delivery_type = "fixed"
        self.assertIsNone(StockPicking.schenker_get_label(picking_for_label))
