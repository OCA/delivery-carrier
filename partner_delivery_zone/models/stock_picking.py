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
            partner = (
                picking.partner_id
                if picking.partner_id.type == "delivery"
                else picking.partner_id.commercial_partner_id
            )
            picking.delivery_zone_id = partner.delivery_zone_id

    def write(self, vals):
        # Update sale order delivery zone if user update it a picking linked
        # to a sale order,
        res = super().write(vals)
        if "delivery_zone_id" in vals and not self.env.context.get(
            "skip_delivery_zone_update", False
        ):
            self.mapped("sale_id").with_context(skip_delivery_zone_update=True).write(
                {"delivery_zone_id": vals["delivery_zone_id"]}
            )
        return res
