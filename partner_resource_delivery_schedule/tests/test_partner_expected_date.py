# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime

from freezegun import freeze_time

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


@freeze_time("2023-12-18")
@tagged("post_install", "-at_install")
class TestPartnerExpectedDate(TransactionCase):
    def setUp(self):
        super(TestPartnerExpectedDate, self).setUp()
        # 2 weeks is enough for testing
        self.env["ir.config_parameter"].sudo().set_param(
            "partner_resource_delivery_schedule.interval_days", "14"
        )
        partner_calendar = self.env["resource.calendar"].create(
            {
                "name": "Fridays from 5 to 19",
                "tz": "UTC",
                "company_id": self.env.company.id,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Friday morning",
                            "dayofweek": "4",
                            "hour_from": 5.0,
                            "hour_to": 19.0,
                            "day_period": "morning",
                        },
                    )
                ],
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Partner with Resource",
                "company_id": None,
            }
        )
        # Check that resource is created when calendar is set and deleted when calendar is unset
        self.partner.action_create_delivery_schedule_resource()
        self.partner.write({"delivery_schedule_calendar_id": partner_calendar.id})
        self.assertEqual(
            self.partner.delivery_schedule_resource_id.calendar_id,
            partner_calendar,
            "Calendar not set on resource",
        )
        self.partner.write({"delivery_schedule_calendar_id": False})
        self.assertFalse(
            self.partner.delivery_schedule_resource_id, "Resource not deleted"
        )
        self.partner.action_create_delivery_schedule_resource()
        self.partner.write({"delivery_schedule_calendar_id": partner_calendar.id})
        self.env["resource.calendar.leaves"].create(
            {
                "name": f"{self.partner.name} leave",
                "resource_id": self.partner.delivery_schedule_resource_id.id,
                "date_from": "2023-12-22 02:00:00",
                "date_to": "2023-12-23 02:00:00",
                "company_id": self.env.company.id,
            }
        )
        self.env.company.resource_calendar_id.write({"tz": "UTC"})
        self.env.company.resource_calendar_id.attendance_ids.filtered_domain(
            [
                ("dayofweek", "=", "4"),
                ("day_period", "=", "morning"),
            ]
        ).write(
            {
                "hour_from": 11.0,
                "hour_to": 12.0,
            }
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Product",
                "list_price": 5,
                "type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        location = self.env["stock.location"].create(
            {"name": "Test location", "usage": "internal"}
        )
        self.env["stock.quant"].create(
            {
                "quantity": 100,
                "location_id": location.id,
                "product_id": self.product.id,
            }
        )

    def _create_partner_order(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "state": "draft",
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                            "product_uom_qty": 10,
                        },
                    )
                ],
            }
        )

    def test_partner_expected_date(self):
        # Create order
        order = self._create_partner_order()
        # Get first available date
        order.calc_next_commitment_date()
        first_available_date = datetime.strptime(
            "2023-12-29 11:00:00", DEFAULT_SERVER_DATETIME_FORMAT
        )
        self.assertEqual(order.commitment_date, first_available_date)
        # Get next available date
        order.calc_next_commitment_date()
        next_available_date = datetime.strptime(
            "2024-01-05 11:00:00", DEFAULT_SERVER_DATETIME_FORMAT
        )
        self.assertEqual(order.commitment_date, next_available_date)
        # Create picking
        order.action_confirm()
        main_picking = order.picking_ids[0]
        self.assertEqual(main_picking.scheduled_date, order.commitment_date)
        self.assertEqual(main_picking.date_deadline, order.commitment_date)
        # Prepare picking to create backorder
        main_picking.move_ids.write({"quantity_done": 5})
        # Prepare picking to trigger a new expected date on the backorder
        main_picking.write({"scheduled_date": "2023-12-17"})
        # Skip backorder wizard and set directly the pickings that needs backorder
        main_picking.with_context(
            button_validate_picking_ids=main_picking.ids, skip_backorder=True
        ).button_validate()
        backorder_picking = order.picking_ids[-1]
        # Because picking has been done after the scheduled date,
        # recomputation of the expected date is the first available date
        self.assertEqual(backorder_picking.scheduled_date, first_available_date)

    def test_partner_commitment_date(self):
        # Create order
        order = self._create_partner_order()
        commitment_date = datetime.strptime(
            "2023-12-22 12:00:00", DEFAULT_SERVER_DATETIME_FORMAT
        )
        order.write({"commitment_date": commitment_date})
        order.action_confirm()
        main_picking = order.picking_ids[0]
        # Ensure that commitment date is propagated to the picking
        self.assertEqual(main_picking.scheduled_date, commitment_date)
        self.assertEqual(main_picking.date_deadline, commitment_date)
