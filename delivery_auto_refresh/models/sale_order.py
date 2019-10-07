# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _auto_refresh_delivery(self, force=False):
        self.ensure_one()
        # Avoid infinite recursion
        if self.env.context.get('force_delivery_set'):  # pragma: no cover
            return self
        get_param = self.env['ir.config_parameter'].sudo().get_param
        param = 'delivery_auto_refresh.auto_add_delivery_line'
        if (force or safe_eval(get_param(param, '0'))) and self.carrier_id:
            if (self.state in {'draft', 'sent'} or
                    self.invoice_shipping_on_delivery):
                self.with_context(force_delivery_set=True).delivery_set()

    def write(self, vals):
        """Refresh delivery price after saving."""
        res = super(SaleOrder, self).write(vals)
        for order in self:
            force = order.order_line.filtered('is_delivery')
            # Make sure that if you have removed the carrier, the line is gone
            if order.state in {'draft', 'sent'}:
                order._delivery_unset()
            order._auto_refresh_delivery(force=force)
        return res
