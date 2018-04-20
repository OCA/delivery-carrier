# -*- coding: utf-8 -*-
# Copyright 2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
from odoo.tools import float_is_zero


class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    @api.multi
    def _roulier_get_unit_price_for_customs(self):
        """This method is designed to be inherited for specific scenarios"""
        self.ensure_one()
        prec = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        if (
                self.linked_move_operation_ids and
                self.linked_move_operation_ids[0].move_id and
                self.linked_move_operation_ids[0].move_id.procurement_id and
                self.linked_move_operation_ids[0].move_id.procurement_id.
                sale_line_id and
                not float_is_zero(
                self.linked_move_operation_ids[0].move_id.procurement_id.
                sale_line_id.product_uom_qty, precision_digits=prec)):
            sol = self.linked_move_operation_ids[0].move_id.\
                procurement_id.sale_line_id
            price_unit_so_uom = sol.price_subtotal / sol.product_uom_qty
            price_unit = sol.product_uom._compute_price(
                price_unit_so_uom, self.product_uom_id)
        else:
            product = self.product_id
            ato = self.env['account.tax']
            price_unit = ato._fix_tax_included_price_company(
                product.list_price, product.taxes_id, ato,
                self.picking_id.company_id)
        return price_unit
