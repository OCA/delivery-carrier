# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime

from freezegun import freeze_time

from odoo.tests import tagged
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.addons.delivery_partner_schedule.tests.test_partner_expected_date import (
    TestPartnerExpectedDate,
)


@freeze_time("2023-12-18")
@tagged("post_install", "-at_install")
class TestCarrierExpectedDate(TestPartnerExpectedDate):
    def setUp(self):
        super(TestCarrierExpectedDate, self).setUp()
        # 3 weeks is enough for testing
        self.env["ir.config_parameter"].sudo().set_param(
            "delivery_partner_schedule.interval_days", "21"
        )
        carrier_resource = self.env["resource.resource"].create(
            {
                "name": "Fridays from 15 to 19",
                "resource_type": "contact",
                "company_id": None,
                "time_efficiency": 100.0,
            }
        )
        carrier_calendar = self.env["resource.calendar"].create(
            {
                "name": "Fridays from 15 to 19",
                "tz": "UTC",
                "company_id": self.env.company.id,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Friday afternoon",
                            "dayofweek": "4",
                            "hour_from": 15.0,
                            "hour_to": 19.0,
                            "day_period": "afternoon",
                        },
                    )
                ],
            }
        )
        product_delivery_normal = self.env["product.product"].create(
            {
                "name": "Delivery product",
                "invoice_policy": "order",
                "type": "service",
                "list_price": 10.0,
                "categ_id": self.env.ref("delivery.product_category_deliveries").id,
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Carrier with Resource",
                "resource_id": carrier_resource.id,
                "company_id": self.env.company.id,
                "delivery_type": "fixed",
                "product_id": product_delivery_normal.id,
            }
        )
        self.carrier.resource_id.write(
            {
                "tz": "UTC",
                "calendar_id": carrier_calendar.id,
            }
        )
        self.env["resource.calendar.leaves"].create(
            {
                "name": f"{self.carrier.name} leave",
                "resource_id": self.carrier.resource_id.id,
                "calendar_id": self.carrier.resource_id.calendar_id.id,
                "date_from": "2023-12-29 02:00:00",
                "date_to": "2023-12-30 02:00:00",
                "company_id": self.env.company.id,
            }
        )

    def _create_carrier_order(self):
        order = self._create_partner_order()
        order.write({"carrier_id": self.carrier.id})
        return order

    def test_carrier_expected_date(self):
        # Create order
        order = self._create_carrier_order()
        expected_date = datetime.strptime(
            "2024-01-05 15:00:00", DEFAULT_SERVER_DATETIME_FORMAT
        )
        order_expected_date = order.expected_date
        self.assertEqual(order_expected_date, expected_date)
        # Create picking
        order.action_confirm()
        main_picking = order.picking_ids[0]
        self.assertEqual(main_picking.scheduled_date, order_expected_date)
        self.assertEqual(main_picking.date_deadline, order_expected_date)
        # Prepare picking to create backorder
        main_picking.move_ids.write({"quantity_done": 5})
        # Prepare picking to trigger a new expected date on the backorder
        main_picking.write({"scheduled_date": "2023-12-17"})
        # Skip backorder wizard and set directly the pickings that needs backorder
        main_picking.with_context(
            button_validate_picking_ids=main_picking.ids, skip_backorder=True
        ).button_validate()
        backorder_picking = order.picking_ids[-1]
        # Because picking has been done after the sccheduled date,
        # recomputation of the expected date is the same expected date
        self.assertEqual(backorder_picking.scheduled_date, order_expected_date)

    def test_carrier_commitment_date(self):
        # Create order
        order = self._create_carrier_order()
        commitment_date = datetime.strptime(
            "2023-12-22 12:00:00", DEFAULT_SERVER_DATETIME_FORMAT
        )
        order.write({"commitment_date": commitment_date})
        order.action_confirm()
        main_picking = order.picking_ids[0]
        # Ensure that commitment date is propagated to the picking
        self.assertEqual(main_picking.scheduled_date, commitment_date)
        self.assertEqual(main_picking.date_deadline, commitment_date)
