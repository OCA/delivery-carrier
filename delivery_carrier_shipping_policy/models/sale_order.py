# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    carrier_id = fields.Many2one(inverse="_inverse_carrier_id")

    def _inverse_carrier_id(self):
        # pylint: disable=missing-return
        if hasattr(super(), "_inverse_carrier_id"):
            super()._inverse_carrier_id()
        for rec in self:
            if rec.carrier_id.picking_policy:
                rec.picking_policy = rec.carrier_id.picking_policy
