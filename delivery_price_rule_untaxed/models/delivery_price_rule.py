# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class DeliveryPriceRule(models.Model):
    _inherit = 'delivery.price.rule'

    variable = fields.Selection(
        selection_add=[('untaxed_price', 'Untaxed price')])
    variable_factor = fields.Selection(
        selection_add=[('untaxed_price', 'Untaxed price')])

    @api.multi
    def is_untaxed_rule(self):
        self.ensure_one()
        return 'untaxed_price' in (self.variable, self.variable_factor)
