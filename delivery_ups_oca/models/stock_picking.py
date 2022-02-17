# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ups_insurance = fields.Boolean(
        string="Manage UPS Insurance",
        help="If checked, we send insurance information to get rate",
    )
    ups_insurance_value = fields.Float(string="Shipping Declared Value",)

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        if self.carrier_id.delivery_type == "ups" and self.carrier_id.ups_insurance:
            self.ups_insurance = self.carrier_id.ups_insurance
            self.ups_insurance_value = sum(
                self.mapped("move_lines.sale_line_id.price_subtotal")
            )
