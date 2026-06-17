# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import Form

from .common import DeliveryScheduleCommon


class TestPartnerDeliverySchedule(DeliveryScheduleCommon):
    @classmethod
    def _setup_partners(cls):
        res = super()._setup_partners()
        # Extra fixtures needed for report tests only
        cls.report_model = cls.env["ir.actions.report"]
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "consu", "is_storable": True}
        )
        cls.order = cls._create_sale_order(cls)
        cls.order.action_confirm()
        cls.picking = cls.order.picking_ids[0]
        return res

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1.0
        return order_form.save()

    def test_partner_schedule_name(self):
        self.assertEqual(
            self.schedule_8h.display_name, "08:00-10:00 (Mo, Tu, We, Th, Fr)"
        )
        day_update = {day[0]: True for day in self.schedule_8h._days_of_week()}
        self.schedule_8h.update(day_update)
        self.assertEqual(self.schedule_8h.display_name, "08:00-10:00 (All days)")
        with self.assertRaises(ValidationError):
            self.schedule_8h.update({"hour_from": 0, "hour_to": 25})
        day_update = {day[0]: False for day in self.schedule_8h._days_of_week()}
        with self.assertRaises(ValidationError):
            self.schedule_8h.update(day_update)

    def test_partner_allow_delivery(self):
        # partner has schedule_8h (08:00-10:00) and schedule_14h (14:00-16:00), Mon-Fri
        self.assertTrue(self.partner.allow_delivery_date("2018-09-03 09:00:00"))
        self.assertTrue(self.partner.allow_delivery_date("2018-09-04 09:00:00"))
        self.assertFalse(self.partner.allow_delivery_date("2018-09-04 12:01:00"))
        self.assertFalse(self.partner.allow_delivery_date("2018-09-05 10:01:00"))
        # Allow delivery on all days
        day_update = {day[0]: True for day in self.schedule_8h._days_of_week()}
        self.schedule_8h.update(day_update)
        self.assertTrue(self.partner.allow_delivery_date("2018-09-09 09:00:00"))

    def test_report_picking(self):
        res = self.report_model._render_qweb_html(
            "stock.report_picking", self.picking.ids, False
        )
        self.assertRegex(str(res[0]), "08:00-10:00")
        self.assertRegex(str(res[0]), "14:00-16:00")

    def test_report_deliveryslip(self):
        res = self.report_model._render_qweb_html(
            "stock.report_deliveryslip", self.picking.ids, False
        )
        self.assertRegex(str(res[0]), "08:00-10:00")
        self.assertRegex(str(res[0]), "14:00-16:00")
