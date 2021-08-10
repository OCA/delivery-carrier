# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from psycopg2 import IntegrityError

from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger


class TestCarrierCategory(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.DeliveryCarrierCateg = cls.env["delivery.carrier.category"]

    def test_code_unique(self):
        vals = {
            "name": "Drop-Off 2",
            "code": "DROP",
        }
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.DeliveryCarrierCateg.create(vals)

    def test_code_unique_archived(self):
        drop_off = self.env.ref(
            "delivery_carrier_category.delivery_carrier_category_dropoff"
        )
        drop_off.active = False
        drop_off.flush()
        vals = {
            "name": "Drop-Off 2",
            "code": drop_off.code,
        }
        self.DeliveryCarrierCateg.create(vals)
