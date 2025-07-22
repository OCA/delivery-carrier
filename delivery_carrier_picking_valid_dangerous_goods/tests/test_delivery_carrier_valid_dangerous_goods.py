# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.delivery_carrier_picking_valid.tests.common import Common


class TestPickingValid(Common):
    @classmethod
    def setUpClass(cls):
        res = super().setUpClass()
        cls.setUpClassDangerousGoods()
        return res

    @classmethod
    def setUpClassDangerousGoods(cls):
        # Create carrier with restriction for products with limited qty,
        # product flagged as limited in quantity, and a picking with that product.
        cls.limited_quantity = cls.env.ref(
            "l10n_eu_product_adr_dangerous_goods.limited_amount_1"
        )
        cls.carrier_limited_quantity = cls._create_carrier(
            "LQ carrier", adr_limited_amount_ids=[(6, 0, cls.limited_quantity.ids)]
        )
        cls.limited_quantity_product = cls.env["product.product"].create(
            {"name": "LQ product", "limited_amount_id": cls.limited_quantity.id}
        )
        cls.limited_qty_picking = cls._create_picking(
            [(cls.limited_quantity_product, 1)]
        )
        # Create carrier with restriction for dangerous goods,
        # product flagged as dangerous, and a picking with that product.
        cls.dangerous_goods = cls.env.ref(
            "l10n_eu_product_adr_dangerous_goods.limited_amount_2"
        )
        cls.carrier_dangerous_goods = cls._create_carrier(
            "DG carrier", adr_limited_amount_ids=[(6, 0, cls.dangerous_goods.ids)]
        )
        cls.dangerous_goods_product = cls.env["product.product"].create(
            {"name": "DG product", "limited_amount_id": cls.dangerous_goods.id}
        )
        cls.dangerous_goods_picking = cls._create_picking(
            [(cls.dangerous_goods_product, 1)]
        )

    def test_match_dangerous_goods(self):
        picking_no_limited_amount = self.picking
        picking_dg_restriction = self.dangerous_goods_picking
        picking_lq_restriction = self.limited_qty_picking
        # both carriers with limited amount are matching this picking, since
        # this picking has no product with limited amount
        self.assertTrue(
            self.carrier_limited_quantity._match_picking(picking_no_limited_amount)
        )
        self.assertTrue(
            self.carrier_dangerous_goods._match_picking(picking_no_limited_amount)
        )
        # carrier with no restriction on limited amounts is matching
        # both pickings with limited amount
        self.assertTrue(
            self.carrier_volume_restriction._match_picking(picking_dg_restriction)
        )
        self.assertTrue(
            self.carrier_volume_restriction._match_picking(picking_lq_restriction)
        )
        self.assertTrue(
            self.carrier_weight_restriction._match_picking(picking_dg_restriction)
        )
        self.assertTrue(
            self.carrier_weight_restriction._match_picking(picking_lq_restriction)
        )
        # dg carrier shouldn't match dg picking, lq carrier shouldn't match dg picking
        self.assertFalse(
            self.carrier_limited_quantity._match_picking(picking_lq_restriction)
        )
        self.assertFalse(
            self.carrier_dangerous_goods._match_picking(picking_dg_restriction)
        )
        # dg carrier should match lq picking, lq carrier should match dg picking
        self.assertTrue(
            self.carrier_limited_quantity._match_picking(picking_dg_restriction)
        )
        self.assertTrue(
            self.carrier_dangerous_goods._match_picking(picking_lq_restriction)
        )
