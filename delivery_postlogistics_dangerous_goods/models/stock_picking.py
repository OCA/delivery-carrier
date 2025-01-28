# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_unnumbers(self, pack=None):
        """
        If any dangerous goods with limited quantity, returns a list of UNNumbers.
        """
        self.ensure_one()
        products = (
            pack
            and pack.mapped("quant_ids.product_id")
            or self.mapped("move_ids.product_id")
        )
        limited_amount_lq = self.env.ref(
            "l10n_eu_product_adr_dangerous_goods.limited_amount_1"
        )
        limited_quantity_products = products.filtered(
            lambda p: p.is_dangerous and p.limited_amount_id == limited_amount_lq
        )
        # Since 14.0, un numbers checks are done directly in l10n_eu_product_adr
        return [
            int(product.adr_goods_id.un_number) for product in limited_quantity_products
        ]

    def postlogistics_label_prepare_attributes(
        self, pack=None, pack_num=None, pack_total=None, pack_weight=None
    ):
        # Adds a new attribute UNNumbers when there's dangerous goods
        # in the pack / picking
        res = super().postlogistics_label_prepare_attributes(
            pack, pack_num, pack_total, pack_weight
        )
        unnumbers = self._get_unnumbers(pack)
        if unnumbers:
            res.setdefault("przl", []).append("LQ")
            res["unnumbers"] = unnumbers
        return res
