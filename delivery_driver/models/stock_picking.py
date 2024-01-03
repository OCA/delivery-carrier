# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        domain="[('is_company', '=', False)]",
        compute="_compute_driver_id",
        store=True,
        readonly=False,
    )

    @api.depends("carrier_id")
    def _compute_driver_id(self):
        for picking in self:
            if picking.state not in {"done", "cancel"}:
                picking.driver_id = picking.carrier_id.driver_id
