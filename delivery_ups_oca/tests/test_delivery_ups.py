# Copyright 2020 Hunki Enterprises BV
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from unittest import mock

from odoo.modules import get_module_resource
from odoo.tests import Form, common

_module_ns = "odoo.addons.delivery_ups_oca"
_provider_class = _module_ns + ".models.ups_request.UpsRequest"


class TestDeliveryUpsBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_shipping_cost = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "UPS",
                "delivery_type": "ups",
                "product_id": product_shipping_cost.id,
                "price_method": "fixed",
                "ups_default_packaging_id": cls.env.ref(
                    "delivery_ups_oca.product_packaging_ups_02"
                ).id,
            }
        )
        cls.company = cls.env.ref("base.main_company")
        cls.company.partner_id.write(
            {
                "phone": "+%s976123456" % cls.company.country_id.phone_code,
                "vat": "%s09915370R" % cls.company.country_id.code,
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
                "vat": cls.company.partner_id.vat,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product", "weight": 10}
        )
        cls.sale = cls._create_sale_order(cls)

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
        sale = order_form.save()
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": self.carrier.id}
            )
        ).save()
        delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale


class TestDeliveryUps(TestDeliveryUpsBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.move_lines.quantity_done = 10

    def test_order_ups_rate_shipment(self):
        with mock.patch(
            _provider_class + "._rate_shipment",
            return_value={
                "RateResponse": {
                    "RatedShipment": {
                        "TotalCharges": {"MonetaryValue": 1, "CurrencyCode": "USD"}
                    }
                }
            },
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            self.assertGreater(res["price"], 0)
            self.assertTrue(res["success"])

    def test_order_ups_rate_shipment_currency_extra(self):
        usd = self.env.ref("base.USD")
        eur = self.env.ref("base.EUR")
        currency = self.env.ref("base.main_company").currency_id
        currency_extra = eur if currency == usd else usd
        self.sale.currency_id = currency_extra
        with mock.patch(
            _provider_class + "._rate_shipment",
            return_value={
                "RateResponse": {
                    "RatedShipment": {
                        "TotalCharges": {"MonetaryValue": 1, "CurrencyCode": "USD"}
                    }
                }
            },
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            self.assertGreater(res["price"], 0)
            self.assertTrue(res["success"])

    def test_delivery_carrier_ups_integration(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        dummy_pdf_path = get_module_resource(
            "delivery_carrier_label_batch", "tests", "dummy.pdf"
        )
        with open(dummy_pdf_path, "rb") as dummy_pdf:
            label = dummy_pdf.read()
            with mock.patch(
                _provider_class + "._send_shipping",
                return_value={
                    "price": {"CurrencyCode": "USD", "MonetaryValue": "0.0"},
                    "ShipmentIdentificationNumber": "123456",
                    "labels": [
                        {
                            "tracking_ref": "123456",
                            "format_code": "png",
                            "datas": base64.b64encode(label),
                        }
                    ],
                },
            ):
                self.picking.send_to_shipper()
                self.assertEqual(self.picking.message_attachment_count, 1)
                self.assertTrue(self.picking.carrier_tracking_ref)
                self.assertFalse(self.picking.tracking_state_history)
                self.assertEqual(
                    self.picking.delivery_state, "shipping_recorded_in_carrier"
                )
                if self.picking.carrier_id.ups_tracking_state_update_sync:
                    with mock.patch(
                        _provider_class + ".tracking_state_update",
                        return_value={
                            "delivery_state": "in_transit",
                            "tracking_state_history": "history",
                        },
                    ):
                        self.picking.tracking_state_update()
                        self.assertEqual(self.picking.delivery_state, "in_transit")
                        self.assertTrue(self.picking.tracking_state_history)
                with mock.patch(
                    _provider_class + ".cancel_shipment",
                    return_value=True,
                ):
                    self.picking.cancel_shipment()
                    self.assertFalse(self.picking.carrier_tracking_ref)
                    self.assertEqual(self.picking.delivery_state, "canceled_shipment")
