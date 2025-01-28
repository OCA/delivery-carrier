# Copyright 2025 BizzAppDev Systems Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError

from .common import TestPostlogisticsCommon


class TestStockPicking(TestPostlogisticsCommon):
    def setUp(self):
        super().setUp()
        self.picking = self.create_picking()
        self.picking.carrier_id = False
        self.picking.delivery_type = "postlogistics"

    def test_action_generate_carrier_label_no_carrier(self):
        """Test that an error is raised when generating a carrier label without a
        carrier."""
        with self.assertRaisesRegex(UserError, "Please, set a carrier."):
            self.picking.action_generate_carrier_label()
