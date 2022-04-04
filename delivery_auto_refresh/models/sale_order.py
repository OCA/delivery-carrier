# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _auto_refresh_delivery(self):
        self.ensure_one()
        # Make sure that if you have removed the carrier, the line is gone
        if self.state in {'draft', 'sent'}:
            self._remove_delivery_line()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        param = 'delivery_auto_refresh.auto_add_delivery_line'
        if safe_eval(get_param(param, '0')) and self.carrier_id:
            if (self.state in {'draft', 'sent'} or
                    self.invoice_shipping_on_delivery):
                price_unit = self.carrier_id.rate_shipment(self)['price']
                self._create_delivery_line(self.carrier_id, price_unit)

    @api.model
    def create(self, vals):
        """Create or refresh delivery line on create."""
        order = super().create(vals)
        order._auto_refresh_delivery()
        return order

    def write(self, vals):
        """Create or refresh delivery line after saving."""
        res = super(SaleOrder, self).write(vals)
        for order in self:
            order._auto_refresh_delivery()
        return res
