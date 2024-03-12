# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        domain="[('is_driver', '=', True)]",
        compute="_compute_driver_id",
        recursive=True,
        store=True,
        readonly=False,
    )

    @api.depends("carrier_id", "move_ids.move_dest_ids.picking_id.driver_id")
    def _compute_driver_id(self):
        for picking in self:
            if picking.state not in {"done", "cancel"}:
                driver = picking.move_ids.mapped("move_dest_ids.picking_id.driver_id")
                picking.driver_id = driver[:1] or picking.carrier_id.driver_id
