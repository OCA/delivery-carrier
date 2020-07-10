# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase


class TestCarrierCategory(TransactionCase):

    def test_code_unique(self):
        vals = {
            "name": "Drop-Off 2",
            "code": "DROP",
        }
        with self.assertRaises(IntegrityError):
            self.env["delivery.carrier.category"].create(vals)

    def test_code_unique_archived(self):
        drop_off = self.env.ref(
            "delivery_carrier_category.delivery_carrier_category_dropoff")
        drop_off.active = False
        vals = {
            "name": "Drop-Off 2",
            "code": "DROP",
        }
        self.env["delivery.carrier.category"].create(vals)
