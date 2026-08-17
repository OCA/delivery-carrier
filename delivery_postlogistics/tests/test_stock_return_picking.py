# Copyright 2025 BizzAppDev Systems Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import Form

from .common import TestPostlogisticsCommon


class TestStockReturnPicking(TestPostlogisticsCommon):
    def setUp(self):
        super().setUp()
        self.picking = self.create_picking()

    def test_create_returns_with_carrier(self):
        """Test that the return picking inherits carrier_id if
        delivery_type is postlogistics."""
        self.picking.action_confirm()
        self.picking.move_ids.picked = True
        self.picking.state = "done"

        # This method calls the API if not already done in the past and
        # when the picking_type print_label is set to True
        self.picking.picking_type_id.print_label = False
        self.picking.button_validate()

        wizard_form = Form(
            self.env["stock.return.picking"].with_context(
                active_id=self.picking.id, active_model="stock.picking"
            )
        )
        wizard = wizard_form.save()
        wizard.product_return_moves.quantity = 3

        action = wizard.action_create_returns()
        return_picking = self.env["stock.picking"].browse(action["res_id"])

        self.assertEqual(
            return_picking.carrier_id,
            self.picking.carrier_id,
            "The return picking should have the same shipping carrier as the original"
            " picking.",
        )
