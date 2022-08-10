# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestDeliveryTntBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier = cls.env["delivery.carrier"].search(
            [("delivery_type", "=", "tnt_oca")]
        )
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.company.partner_id.country_id.id,
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
            {
                "name": "Test product",
                "type": "product",
                "weight": 1,
                "volume": 1,
                "product_length": 1,
                "product_width": 1,
                "product_height": 1,
                "sale_delay": 3,
            }
        )
        cls.sale = cls._create_sale_order(cls)

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
        sale = order_form.save()
        if self.carrier:
            delivery_wizard = Form(
                self.env["choose.delivery.carrier"].with_context(
                    {"default_order_id": sale.id, "default_carrier_id": self.carrier.id}
                )
            ).save()
            delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale


class DeliveryTnt(TestDeliveryTntBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.move_lines.quantity_done = 1

    def test_order_tnt_oca_rate_shipment(self):
        if not self.carrier or self.carrier.prod_environment:
            self.skipTest("Without TNT carrier created")
        res = self.carrier.tnt_oca_rate_shipment(self.sale)
        self.assertGreater(res["price"], 0)
        self.assertTrue(res["success"])

    def test_order_tnt_oca_rate_shipment_error(self):
        if not self.carrier or self.carrier.prod_environment:
            self.skipTest("Without TNT carrier created")
        self.product.volume = 0
        with self.assertRaises(UserError):
            self.carrier.tnt_oca_rate_shipment(self.sale)

    def test_order_tnt_oca_rate_shipment_currency_extra(self):
        if not self.carrier or self.carrier.prod_environment:
            self.skipTest("Without TNT carrier created")
        usd = self.env.ref("base.USD")
        eur = self.env.ref("base.EUR")
        currency = self.env.company.currency_id
        currency_extra = eur if currency == usd else usd
        self.sale.currency_id = currency_extra
        res = self.carrier.tnt_oca_rate_shipment(self.sale)
        self.assertGreater(res["price"], 0)
        self.assertTrue(res["success"])

    def test_delivery_carrier_tnt_oca_integration(self):
        if not self.carrier or self.carrier.prod_environment:
            self.skipTest("Without TNT carrier created")
        self.picking.action_confirm()
        self.picking.action_assign()
        # Increase +1 day to prevent error according from today
        new_date = self.picking.scheduled_date + timedelta(days=1)
        if new_date.weekday() == 5:
            new_date += timedelta(days=2)
        elif new_date.weekday() == 6:
            new_date += timedelta(days=1)
        self.picking.scheduled_date = new_date
        self.picking.send_to_shipper()
        self.assertEquals(self.picking.message_attachment_count, 1)
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.tracking_state_history)
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.picking.tracking_state_update()
        self.assertEqual(self.picking.tracking_state_history, "CNF")
        with self.assertRaises(NotImplementedError):
            self.picking.cancel_shipment()
            self.assertEqual(self.picking.tracking_state_history, "CNF")

    def test_delivery_carrier_tnt_oca_integration_error(self):
        if not self.carrier or self.carrier.prod_environment:
            self.skipTest("Without TNT carrier created")
        self.picking.action_confirm()
        self.picking.action_assign()
        new_date = self.picking.scheduled_date + timedelta(days=-1)
        self.picking.scheduled_date = new_date
        with self.assertRaises(UserError):
            self.picking.send_to_shipper()
