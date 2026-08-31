# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ups_landed_cost_quote_identifier = fields.Char(
        string="UPS Global Checkout Quote ID",
        help="Quote ID from UPS Global Checkout, copied from the sale order. It is "
        "sent to UPS at shipment creation so the guaranteed duties and taxes are "
        "linked to this shipment.",
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Copy the UPS Global Checkout Quote ID from the originating sale order."""
        pickings = super().create(vals_list)
        for picking in pickings:
            if (
                picking.carrier_id.delivery_type == "ups"
                and not picking.ups_landed_cost_quote_identifier
                and picking.sale_id.ups_landed_cost_quote_identifier
            ):
                picking.ups_landed_cost_quote_identifier = (
                    picking.sale_id.ups_landed_cost_quote_identifier
                )
        return pickings

    def ups_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "ups" or not tracking_ref:
            return
        return self.carrier_id.ups_get_label(tracking_ref)
