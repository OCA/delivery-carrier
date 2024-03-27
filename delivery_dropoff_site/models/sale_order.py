# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    dropoff_site_required = fields.Boolean(
        string="Drop-off Site Required",
        store=True,
        related="carrier_id.with_dropoff_site",
    )
    final_shipping_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Final Recipient",
        states={"done": [("readonly", True)], "cancel": [("readonly", True)]},
        readonly=False,
        help="It is the partner that will pick up the parcel in the dropoff site.",
    )
    allowed_partner_shipping_ids = fields.Many2many(
        "res.partner", compute="_compute_allowed_partner_shipping_ids"
    )

    @api.onchange("carrier_id")
    def onchange_carrier_id(self):
        carrier = self.carrier_id
        partner = self.partner_shipping_id
        if (
            carrier
            and partner
            and (
                carrier.with_dropoff_site != partner.is_dropoff_site
                or (
                    carrier.with_dropoff_site
                    and partner.dropoff_site_carrier_id != carrier
                )
            )
        ):
            self.partner_shipping_id = False

    @api.onchange("partner_shipping_id", "partner_id", "company_id")
    def onchange_partner_shipping_id(self):
        super().onchange_partner_shipping_id()
        if (
            self.partner_shipping_id
            and self.partner_shipping_id.dropoff_site_id
            and not self.final_shipping_partner_id
        ):
            self.final_shipping_partner_id = self.partner_id

    @api.depends("carrier_id", "carrier_id.with_dropoff_site")
    def _compute_allowed_partner_shipping_ids(self):
        for sale in self:
            if sale.carrier_id and sale.carrier_id.with_dropoff_site:
                allowed_partner_shipping_ids = self.env["res.partner"].search(
                    [("dropoff_site_carrier_id", "=", sale.carrier_id.id)]
                )
            else:
                allowed_partner_shipping_ids = self.env["res.partner"].search(
                    [("is_dropoff_site", "=", False)]
                )
            sale.allowed_partner_shipping_ids = allowed_partner_shipping_ids


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id):
        res = super()._prepare_procurement_values(group_id=group_id)
        res.update(
            {
                "final_shipping_partner_id": self.order_id.final_shipping_partner_id.id,
            }
        )
        return res
