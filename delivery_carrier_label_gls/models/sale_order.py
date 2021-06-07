# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    gls_parcel_shop = fields.Char(
        "GLS Parcel Shop Identifier", help="Fill this for a delivery to a ParcelShop.",
    )
    delivery_type = fields.Selection(related="carrier_id.delivery_type", readonly=True)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for so in self:
            if so.gls_parcel_shop:
                so.picking_ids.update({"gls_parcel_shop": so.gls_parcel_shop})
        return res
