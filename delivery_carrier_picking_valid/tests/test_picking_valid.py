# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import Common


class TestPickingValid(Common):
    def test_match_volume(self):
        picking = self.picking
        # volume of picking is 2
        self.assertTrue(self.carrier_no_restriction._match_picking_volume(picking))
        # carrier_volume_restriction accepts pickings up to 1m3
        self.assertFalse(self.carrier_volume_restriction._match_picking_volume(picking))

    def test_match_weight(self):
        picking = self.picking
        # weight of picking is 2
        self.assertTrue(self.carrier_no_restriction._match_picking_weight(picking))
        # carrier_weight_restriction accepts pickings up to 1kg
        self.assertFalse(self.carrier_weight_restriction._match_picking_weight(picking))

    def test_match_picking(self):
        picking = self.picking
        # Just an aggregate of what's above
        self.assertTrue(self.carrier_no_restriction._match_picking(picking))
        self.assertFalse(self.carrier_volume_restriction._match_picking(picking))
        self.assertFalse(self.carrier_weight_restriction._match_picking(picking))
