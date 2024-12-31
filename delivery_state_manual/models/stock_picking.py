# Copyright 2024 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_state = fields.Selection(
        readonly=False,
        help="This field is set automatically unless the delivery carrier is marked as manual. "
        "If manually edited, the carrier dates will be updated",
    )
    delivery_state_manual = fields.Boolean(related="carrier_id.delivery_state_manual")

    @api.onchange("delivery_state")
    def _onchange_delivery_state(self):
        for rec in self.filtered("delivery_state_manual"):
            rec.date_delivered = (
                datetime.datetime.now()
                if rec.delivery_state in ["customer_delivered", "warehouse_delivered"]
                else False
            )
            if rec.delivery_state == "shipping_recorded_in_carrier":
                rec.date_shipped = datetime.datetime.now()
            elif rec.delivery_state == "canceled_shipment":
                rec.date_shipped = False
