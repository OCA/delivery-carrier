# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import api, fields, models


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    driver_ids = fields.Many2many(
        "res.partner",
        string="Drivers",
        compute="_compute_driver_ids",
        store=True,
        domain="[('is_company', '=', False)]",
    )

    @api.depends("picking_ids.driver_id")
    def _compute_driver_ids(self):
        for batch in self:
            batch.driver_ids = batch.picking_ids.mapped("driver_id")
