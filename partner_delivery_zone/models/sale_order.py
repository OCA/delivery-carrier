# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_zone_id = fields.Many2one(
        comodel_name="partner.delivery.zone",
        string="Delivery Zone",
        ondelete="restrict",
        compute="_compute_delivery_zone_id",
        store=True,
        readonly=False,
        index=True,
    )

    @api.depends("partner_shipping_id")
    def _compute_delivery_zone_id(self):
        for so in self:
            partner = (
                so.partner_shipping_id
                if so.partner_shipping_id.type == "delivery"
                else so.partner_shipping_id.commercial_partner_id
            )
            so.delivery_zone_id = partner.delivery_zone_id

    def write(self, vals):
        # Update picking delivery zone if user update it in sale order that
        # creates a picking,
        res = super().write(vals)
        if "delivery_zone_id" in vals and not self.env.context.get(
            "skip_delivery_zone_update", False
        ):
            self.mapped("picking_ids").with_context(
                skip_delivery_zone_update=True
            ).write({"delivery_zone_id": vals["delivery_zone_id"]})
        return res
