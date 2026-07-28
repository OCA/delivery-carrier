# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestPartnerDeliveryZoneCalendar(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Dummy calendar",
            }
        )
        cls.pdz = cls.env["partner.delivery.zone"].create(
            {
                "code": "PDZ",
                "name": "Dummy partner delivery zone",
            }
        )

    def test_dummy(self):
        self.pdz.calendar_id = self.calendar.id
        self.assertEqual(self.pdz.calendar_id, self.calendar)
