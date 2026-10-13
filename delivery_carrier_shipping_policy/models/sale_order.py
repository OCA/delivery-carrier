# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    carrier_id = fields.Many2one(inverse="_inverse_carrier_id")

    def _inverse_carrier_id(self):
        res = (
            super()._inverse_carrier_id()
            if hasattr(super(), "_inverse_carrier_id")
            else False
        )
        for rec in self:
            if rec.carrier_id.picking_policy:
                rec.picking_policy = rec.carrier_id.picking_policy
        return res
