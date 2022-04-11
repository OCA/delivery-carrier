# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DeliveryPriceRule(models.Model):
    _inherit = "delivery.price.rule"

    variable = fields.Selection(
        selection_add=[("untaxed_price", "Untaxed price")],
        ondelete={"untaxed_price": "cascade"},
    )
    variable_factor = fields.Selection(
        selection_add=[("untaxed_price", "Untaxed price")],
        ondelete={"untaxed_price": "cascade"},
    )

    def is_untaxed_rule(self):
        self.ensure_one()
        return "untaxed_price" in (self.variable, self.variable_factor)
