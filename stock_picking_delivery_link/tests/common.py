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
        cls.shelf1_loc = cls.env["stock.location"].create(
            {
                "name": "Shelf 1",
                "location_id": cls.stock_loc.id,
            }
        )
        cls.shelf2_loc = cls.env["stock.location"].create(
            {
                "name": "Shelf 2",
                "location_id": cls.stock_loc.id,
            }
        )

    def _create_move(self, product, src_location, dst_location, **values):
        move_values = {
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": 1.0,
            "location_id": src_location.id,
            "location_dest_id": dst_location.id,
        }
        move_values.update(**values)
        return self.env["stock.move"].create(move_values)
