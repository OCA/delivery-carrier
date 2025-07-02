# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.delivery_carrier_picking_valid.tests.common import Common


class TestPickingValid(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpClassPackaging()

    @classmethod
    def setUpClassPackaging(cls):
        cls.pair_packaging = cls.env["product.packaging"].create(
            {"name": "pair", "product_id": cls.product.id, "qty": 2, "weight": 4.0}
        )
        cls.cardbox_packaging = cls.env["product.packaging"].create(
            {
                "name": "cardbox",
                "product_id": cls.product.id,
                "qty": 10,
                "weight": 40.0,
            }
        )

    def test_match_weight(self):
        # Same test as in delivery_carrier_picking_valid,
        # should yield the same result
        picking = self.picking
        # weight of picking is 2
        self.assertTrue(self.carrier_no_restriction._match_picking_weight(picking))
        # carrier_volume_restriction accepts pickings up to 1m3
        self.assertFalse(self.carrier_weight_restriction._match_picking_weight(picking))

    def test_read_group(self):
        domain = [("id", "in", self.picking.move_ids.ids)]
        fields = ["estimated_shipping_weight"]
        groupby = ["picking_id"]
        res = self.env["stock.move"].read_group(domain, fields, groupby)
        self.assertEqual(res[0]["estimated_shipping_weight"], 2.0)
