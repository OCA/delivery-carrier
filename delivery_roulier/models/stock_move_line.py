# Copyright 2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import float_is_zero


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def get_unit_price_for_customs(self):
        """This method is designed to be inherited for specific scenarios"""
        self.ensure_one()
        prec = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        soline = self.get_sale_order_line()
        if soline and not float_is_zero(soline.product_uom_qty, precision_digits=prec):
            price_unit_so_uom = soline.price_subtotal / soline.product_uom_qty
            price_unit = soline.product_uom._compute_price(
                price_unit_so_uom, self.product_uom_id
            )
        else:
            product = self.product_id
            ato = self.env["account.tax"]
            price_unit = ato._fix_tax_included_price_company(
                product.list_price, product.taxes_id, ato, self.picking_id.company_id
            )
        return price_unit

    def get_sale_order_line(self):
        self.ensure_one()
        return self.move_id.sale_line_id
