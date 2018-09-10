# -*- coding: utf-8 -*-
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class PriceRule(models.Model):
    _inherit = "delivery.price.rule"

    product_category_id = fields.Many2one(
        comodel_name='product.category', string='Product category')
    product_category_price = fields.Float(
        string='Category price', digits=dp.get_precision('Product Price'),
        default=0.0, required=True)

    @api.onchange('product_category_price')
    def _onchange_product_category_price(self):
        self.list_base_price = self.product_category_price

    @api.depends('variable', 'operator', 'max_value', 'list_base_price',
                 'list_price', 'variable_factor', 'product_category_id')
    def _get_name(self):
        res = super(PriceRule, self)._get_name()
        for rule in self:
            if rule.product_category_id:
                rule.name = "if category is %s" \
                            % rule.product_category_id.display_name
        return res
