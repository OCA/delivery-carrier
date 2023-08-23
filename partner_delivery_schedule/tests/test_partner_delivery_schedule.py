# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import Form, SavepointCase


class TestPartnerDeliverySchedule(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.schedule = cls.env["delivery.schedule"].create(
            {
                "name": "test",
                "hour_from": 8,
                "hour_to": 10,
                "monday": True,
                "tuesday": True,
                "wednesday": False,
                "thursday": False,
                "friday": False,
            }
        )
        cls.schedule2 = cls.env["delivery.schedule"].create(
            {
                "name": "test2",
                "hour_from": 10,
                "hour_to": 12,
                "monday": True,
                "tuesday": True,
                "wednesday": False,
                "thursday": False,
                "friday": False,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "test",
                "delivery_schedule_ids": [(6, 0, cls.schedule.ids + cls.schedule2.ids)],
            }
        )
        cls.report_model = cls.env["ir.actions.report"]
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls.order = cls._create_sale_order(cls)
        cls.order.action_confirm()
        cls.picking = cls.order.picking_ids[0]

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1.0
        return order_form.save()

    def test_partner_schedule_name(self):
        self.assertEqual(self.schedule.name_get()[0][1], "08:00-10:00 (Mo, Tu)")

        day_update = {}
        for day in self.schedule._days_of_week():
            day_update[day[0]] = True
        self.schedule.update(day_update)
        self.assertEqual(self.schedule.name_get()[0][1], "08:00-10:00 (All days)")

        with self.assertRaises(ValidationError):
            self.schedule.update({"hour_from": 0, "hour_to": 25})

        day_update = {}
        for day in self.schedule._days_of_week():
            day_update[day[0]] = False
        with self.assertRaises(ValidationError):
            self.schedule.update(day_update)

    def test_partner_allow_delivery(self):
        self.assertTrue(self.partner.allow_delivery_date("2018-09-03 09:00:00"))
        self.assertTrue(self.partner.allow_delivery_date("2018-09-04 09:00:00"))
        self.assertFalse(self.partner.allow_delivery_date("2018-09-04 12:01:00"))
        self.assertFalse(self.partner.allow_delivery_date("2018-09-05 10:01:00"))

        # Allow delivery in all days
        day_update = {}
        for day in self.schedule._days_of_week():
            day_update[day[0]] = True
        self.schedule.update(day_update)
        self.assertTrue(self.partner.allow_delivery_date("2018-09-09 09:00:00"))

    def test_report_picking(self):
        res = self.report_model._get_report_from_name(
            "stock.report_picking"
        )._render_qweb_text(self.picking.ids, False)
        self.assertRegex(str(res[0]), "08:00-10:00")
        self.assertRegex(str(res[0]), "10:00-12:00")

    def test_report_deliveryslip(self):
        res = self.report_model._get_report_from_name(
            "stock.report_deliveryslip"
        )._render_qweb_text(self.picking.ids, False)
        self.assertRegex(str(res[0]), "08:00-10:00")
        self.assertRegex(str(res[0]), "10:00-12:00")
