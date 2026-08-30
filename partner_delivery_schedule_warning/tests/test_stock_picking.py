# Copyright 2026 NICO SOLUTIONS - Nils Coenen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class TestStockPicking(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.product = cls.env["product.product"].create({"name": "Test Product"})

        cls.schedule_monday = cls.env["delivery.schedule"].create(
            {
                "name": "Monday 09-10",
                "hour_from": 9.0,
                "hour_to": 10.0,
                "monday": True,
                "tuesday": False,
                "wednesday": False,
                "thursday": False,
                "friday": False,
            }
        )

        cls.schedule_tuesday = cls.env["delivery.schedule"].create(
            {
                "name": "Tuesday 13-14",
                "hour_from": 13.0,
                "hour_to": 14.0,
                "monday": False,
                "tuesday": True,
                "wednesday": False,
                "thursday": False,
                "friday": False,
            }
        )

        cls.partner.delivery_schedule_ids = [
            (4, cls.schedule_monday.id),
            (4, cls.schedule_tuesday.id),
        ]

        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    def setUp(self):
        super().setUp()
        self.picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "scheduled_date": fields.Datetime.to_string(
                    datetime.datetime(2026, 2, 2, 8, 0, 0)
                ),
            }
        )

    def _set_scheduled_date(self, naive_dt):
        """Set scheduled_date using naive datetime (partner local time)"""
        self.picking.scheduled_date = fields.Datetime.to_string(naive_dt)

    def test_no_warning_for_in_schedule_date(self):
        dt = datetime.datetime(2026, 2, 2, 9, 0, 0)
        self._set_scheduled_date(dt)
        dt_str = fields.Datetime.to_string(dt)
        self.assertTrue(self.partner.allow_delivery_date(dt_str))
        self.assertEqual(self.picking.partner_delivery_schedule_warning, "")

    def test_warning_for_out_of_schedule_date(self):
        dt = datetime.datetime(2026, 2, 7, 10, 0, 0)  # Sonntag
        self._set_scheduled_date(dt)
        dt_str = fields.Datetime.to_string(dt)
        self.assertFalse(self.partner.allow_delivery_date(dt_str))
        warning = self.picking.partner_delivery_schedule_warning
        self.assertTrue(warning)
        self.assertIn("09:00-10:00", warning)
        self.assertIn("13:00-14:00", warning)

    def test_warning_at_hour_boundaries(self):
        start = datetime.datetime(2026, 2, 2, 9, 0, 0)
        self._set_scheduled_date(start)
        self.assertTrue(
            self.partner.allow_delivery_date(fields.Datetime.to_string(start))
        )
        end = datetime.datetime(2026, 2, 2, 10, 0, 0)
        self._set_scheduled_date(end)
        self.assertFalse(
            self.partner.allow_delivery_date(fields.Datetime.to_string(end))
        )

    def test_warning_for_wrong_weekday(self):
        dt = datetime.datetime(2026, 2, 4, 10, 0, 0)
        self._set_scheduled_date(dt)
        dt_str = fields.Datetime.to_string(dt)
        self.assertFalse(self.partner.allow_delivery_date(dt_str))
        self.assertTrue(self.picking.partner_delivery_schedule_warning)

    def test_picking_steps_computation(self):
        steps = self.picking.get_steps_list()
        self.assertTrue(steps)
        step_names = [s["step_name_eng"] for s in steps]
        self.assertIn("Delivery", step_names)
        for s in steps:
            self.assertIn("scheduled_date", s)

        for s in steps:
            self.assertIn("delay_from", s)
            self.assertIn("delay_days", s)

    def test_final_step_datetime(self):
        final_dt = self.picking._get_final_step_datetime()
        self.assertIsNotNone(final_dt)
        self.assertGreaterEqual(
            final_dt, fields.Datetime.from_string(self.picking.scheduled_date)
        )

    def test_following_pickings_info_variants(self):
        info = self.picking._get_following_pickings_info()
        self.assertTrue(info)
        for step_name, _step_code, dt, delay in info:
            self.assertIn(
                step_name,
                [
                    "Pick",
                    "Pack",
                    "Delivery",
                    self.picking.picking_type_id.name,
                ],
            )
            self.assertIsInstance(dt, datetime.datetime)
            self.assertIsInstance(delay, (int, float))

    def test_pickings_schedule_info_string(self):
        info_str = self.picking._get_pickings_schedule_info()
        self.assertIsInstance(info_str, str)
        self.assertTrue(info_str)
        self.assertIn("Planned date", info_str)
        self.assertIn("Delivery", info_str)

    def test_partner_pickings_schedule_info_set_when_ok(self):
        dt = datetime.datetime(2026, 2, 2, 9, 0, 0)
        self._set_scheduled_date(dt)
        self.assertEqual(self.picking.partner_delivery_schedule_warning, "")
        info_str = self.picking.partner_pickings_schedule_info
        self.assertTrue(info_str)
        self.assertIn("Planned date", info_str)
        self.assertIn("Delivery", info_str)

    def test_partner_pickings_schedule_info_warning_when_out(self):
        dt = datetime.datetime(2026, 2, 2, 11, 0, 0)
        self._set_scheduled_date(dt)
        warning = self.picking.partner_delivery_schedule_warning
        self.assertTrue(warning)
        self.assertIn("Monday 09-10", warning)
        self.assertIn("Tuesday 13-14", warning)

    def test_picking_steps_with_two_route_steps_and_delay(self):
        warehouse = self.picking_type_out.warehouse_id
        warehouse.write({"delivery_steps": "pick_ship"})
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        picking = order.picking_ids[0]
        route_rules = picking.move_ids.mapped("rule_id.route_id.rule_ids")
        for rule in route_rules:
            rule.delay = 2

        picking._compute_picking_steps()
        steps = picking.get_steps_list()
        self.assertEqual(len(steps), 2)
        delayed_steps = [s for s in steps if s.get("delay_from_eng")]
        self.assertTrue(delayed_steps, "Expected at least one step with delay")
        self.assertIn(2, [s.get("delay_days") for s in steps if s.get("delay_days")])

    def test_picking_steps_with_three_route_steps_and_delay(self):
        warehouse = self.picking_type_out.warehouse_id
        warehouse.write({"delivery_steps": "pick_pack_ship"})
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        picking = order.picking_ids[0]
        route_rules = picking.move_ids.mapped("rule_id.route_id.rule_ids")
        for rule in route_rules:
            rule.delay = 2

        picking._compute_picking_steps()
        steps = picking.get_steps_list()
        self.assertEqual(len(steps), 3)
        delayed_steps = [s for s in steps if s.get("delay_from_eng")]
        self.assertTrue(delayed_steps, "Expected at least one step with delay")
        self.assertIn(2, [s.get("delay_days") for s in steps if s.get("delay_days")])

    def test_compute_picking_steps_skips_unmatched_step_real_data(self):
        warehouse = self.picking_type_out.warehouse_id
        warehouse.write({"delivery_steps": "pick_ship"})
        dummy_type = self.env["stock.picking.type"].create(
            {
                "name": "DummyStep",
                "code": "internal",
                "warehouse_id": warehouse.id,
                "sequence_code": "DUMMY",
            }
        )
        location_dest = warehouse.lot_stock_id
        route = self.env["stock.route"].create({"name": "Test Route"})
        rule = self.env["stock.rule"].create(
            {
                "name": "DummyRule",
                "route_id": route.id,
                "picking_type_id": dummy_type.id,
                "location_dest_id": location_dest.id,
            }
        )
        move = self.picking.move_ids[:1]
        move.rule_id = rule
        self.picking._compute_picking_steps()
        steps = self.picking.get_steps_list()
        step_names = [s["step_name_eng"] for s in steps]
        self.assertIn("Delivery", step_names)
        self.assertNotIn("DummyStep", step_names)

    def test_get_final_step_datetime_no_steps(self):
        empty_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "scheduled_date": fields.Datetime.to_string(
                    datetime.datetime(2026, 2, 2, 8, 0, 0)
                ),
            }
        )
        empty_picking.picking_steps = "[]"
        self.assertIsNone(empty_picking._get_final_step_datetime())

    def test_compute_warning_no_partner_or_done_cancel(self):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": False,
                "picking_type_id": self.picking_type_out.id,
                "scheduled_date": fields.Datetime.to_string(
                    datetime.datetime(2026, 2, 2, 8, 0, 0)
                ),
            }
        )
        picking._compute_partner_delivery_schedule_warning()
        self.assertEqual(picking.partner_delivery_schedule_warning, "")
        self.assertEqual(picking.partner_pickings_schedule_info, "")
        self.picking.state = "done"
        self.picking._compute_partner_delivery_schedule_warning()
        self.assertEqual(self.picking.partner_delivery_schedule_warning, "")

    def test_compute_warning_no_final_dt(self):
        empty_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "scheduled_date": fields.Datetime.to_string(
                    datetime.datetime(2026, 2, 2, 8, 0, 0)
                ),
            }
        )
        empty_picking.picking_steps = "[]"
        empty_picking._compute_partner_delivery_schedule_warning()
        self.assertEqual(
            empty_picking.partner_delivery_schedule_warning,
            "No final step datetime available.",
        )

    def test_compute_warning_no_partner_schedule(self):
        partner_no_schedule = self.env["res.partner"].create({"name": "No Schedule"})
        picking = self.env["stock.picking"].create(
            {
                "partner_id": partner_no_schedule.id,
                "picking_type_id": self.picking_type_out.id,
                "scheduled_date": fields.Datetime.to_string(
                    datetime.datetime(2026, 2, 2, 8, 0, 0)
                ),
            }
        )
        picking._compute_partner_delivery_schedule_warning()
        self.assertIn(
            "INFO: No delivery schedule defined for partner",
            picking.partner_pickings_schedule_info,
        )

    def test_get_pickings_schedule_info_variants(self):
        warehouse = self.picking_type_out.warehouse_id
        warehouse.write({"delivery_steps": "pick_ship"})
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        picking = order.picking_ids[0]
        for rule in picking.move_ids.mapped("rule_id.route_id.rule_ids"):
            rule.delay = 3

        picking._compute_picking_steps()
        info_str = picking._get_pickings_schedule_info()
        self.assertIn("Delay from", info_str)
        self.assertIn("3 day(s)", info_str)

        dt = datetime.datetime(2026, 2, 2, 9, 0, 0)
        picking.scheduled_date = fields.Datetime.to_string(dt)
        info_str = picking._get_pickings_schedule_info()
        self.assertIn("**Monday 09-10:", info_str)

        original_code = self.picking_type_out.code
        self.picking_type_out.code = "internal"
        info_str = picking._get_pickings_schedule_info()
        self.assertIn("Planned dates based on route delay(s):", info_str)
        self.picking_type_out.code = original_code
