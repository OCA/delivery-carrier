# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_zone_id = fields.Many2one(
        comodel_name="partner.delivery.zone",
        string="Delivery Zone",
        index=True,
        store=True,
        readonly=False,
        compute="_compute_delivery_zone_id",
    )

    @api.depends("partner_id")
    def _compute_delivery_zone_id(self):
        for picking in self:
            if picking.partner_id.delivery_zone_id:
                picking.delivery_zone_id = picking.partner_id.delivery_zone_id
