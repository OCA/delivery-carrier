# Copyright 2020-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class StockPickingDeliveryLinkCommonCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.wh = cls.env.ref("stock.warehouse0")

        cls.stock_loc = cls.wh.lot_stock_id
        # own locations: no demo data needed, and no real picking of the
        # database can be reused when the test moves are assigned
        cls.shelf1_loc = cls._create_location("Test shelf 1")
        cls.shelf2_loc = cls._create_location("Test shelf 2")

    @classmethod
    def _create_location(cls, name):
        return cls.env["stock.location"].create(
            {"name": name, "location_id": cls.stock_loc.id}
        )

    def _create_move(self, product, src_location, dst_location, **values):
        Move = self.env["stock.move"]
        # simulate create + onchange
        move = Move.new(
            {
                "product_id": product.id,
                "location_id": src_location.id,
                "location_dest_id": dst_location.id,
            }
        )
        move._onchange_product_id()
        move_values = move._convert_to_write(move._cache)
        move_values.update(**values)
        return Move.create(move_values)
