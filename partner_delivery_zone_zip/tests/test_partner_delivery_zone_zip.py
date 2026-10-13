# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from psycopg2 import IntegrityError

from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestEriPartnerDeliveryZoneZip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.delivery_zone = cls.env["partner.delivery.zone"].create(
            {
                "name": "delivery zone test",
            }
        )
        cls.zip = cls.env["partner.delivery.zone.zip"].create(
            {
                "name": "test zip",
                "delivery_zone_id": cls.delivery_zone.id,
            }
        )
        cls.partner_form = Form(cls.env["res.partner"])

    def test_onchange_zip(self):
        self.assertNotEqual(
            self.partner_form.delivery_zone_id,
            self.delivery_zone,
        )
        self.partner_form.zip = "test zip"
        self.assertEqual(
            self.partner_form.delivery_zone_id,
            self.delivery_zone,
        )

    @mute_logger("odoo.sql_db")
    def test_constraint(self):
        with self.assertRaises(IntegrityError):
            self.zip = self.env["partner.delivery.zone.zip"].create(
                {
                    "name": "test zip",
                    "delivery_zone_id": self.delivery_zone.id,
                }
            )
