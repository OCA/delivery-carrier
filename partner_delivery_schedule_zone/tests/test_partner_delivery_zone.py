# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests import tagged

from .common import DeliveryZoneScheduleCommon


@tagged("post_install", "-at_install")
class TestPartnerDeliveryZone(DeliveryZoneScheduleCommon):
    def test_zone_has_schedules(self):
        """A zone can have multiple schedules linked."""
        self.assertIn(self.schedule_8h, self.delivery_zone_a.delivery_schedule_ids)
        self.assertIn(self.schedule_14h, self.delivery_zone_a.delivery_schedule_ids)

    def test_zone_without_schedules(self):
        """A zone can exist without schedules."""
        self.assertFalse(self.zone_empty.delivery_schedule_ids)

    def test_schedule_shared_across_zones(self):
        """A single schedule can be linked to multiple zones."""
        zone2 = self.env["partner.delivery.zone"].create(
            {
                "name": "Multi-schedule Zone 2",
                "code": "MSZ2",
                "delivery_schedule_ids": [
                    (4, self.schedule_8h.id),
                    (4, self.schedule_sat.id),
                ],
            }
        )
        self.assertIn(self.schedule_8h, self.delivery_zone_a.delivery_schedule_ids)
        self.assertIn(self.schedule_8h, zone2.delivery_schedule_ids)

    def test_add_schedule_to_existing_zone(self):
        """Schedules can be added to an existing zone."""
        self.delivery_zone_b.write(
            {"delivery_schedule_ids": [(4, self.schedule_14h.id)]}
        )
        self.assertIn(self.schedule_14h, self.delivery_zone_b.delivery_schedule_ids)

    def test_remove_schedule_from_zone(self):
        """Schedules can be removed from a zone."""
        self.delivery_zone_a.write(
            {"delivery_schedule_ids": [(3, self.schedule_8h.id)]}
        )
        self.assertNotIn(self.schedule_8h, self.delivery_zone_a.delivery_schedule_ids)
        self.assertIn(self.schedule_14h, self.delivery_zone_a.delivery_schedule_ids)

    def test_partner_with_zone_has_indirect_schedules(self):
        """A partner linked to a zone has access to the zone's schedules."""
        self.assertEqual(self.partner_a.delivery_zone_id, self.delivery_zone_a)
        zone_schedules = self.partner_a.delivery_zone_id.delivery_schedule_ids
        self.assertIn(self.schedule_8h, zone_schedules)
        self.assertIn(self.schedule_14h, zone_schedules)
