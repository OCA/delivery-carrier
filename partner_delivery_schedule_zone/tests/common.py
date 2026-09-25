# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.partner_delivery_schedule.tests.common import DeliveryScheduleCommon
from odoo.addons.partner_delivery_zone.tests.common import DeliveryZoneCommon


class DeliveryZoneScheduleCommon(DeliveryZoneCommon, DeliveryScheduleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = "UTC"

    @classmethod
    def _setup_zones(cls):
        result = super()._setup_zones()
        Zone = cls.env["partner.delivery.zone"]
        cls.delivery_zone_a.delivery_schedule_ids = [
            (4, cls.schedule_8h.id),
            (4, cls.schedule_14h.id),
        ]
        cls.delivery_zone_b.delivery_schedule_ids = [(4, cls.schedule_sat.id)]
        cls.zone_empty = Zone.create({"name": "Delivery Zone Empty", "code": "EMP"})
        return result
