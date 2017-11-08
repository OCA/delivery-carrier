# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from collections import defaultdict

from odoo import api, models, fields


class StockPickingRatePurchase(models.TransientModel):
    """ Purchase a set of stock rates """

    _name = "stock.picking.rate.purchase"
    _inherit = 'stock.picking.rate.wizard.abstract'
    _description = 'Stock Picking Dispatch Rate Purchase'

    date_po = fields.Datetime(
        string='Purchase Order Date',
        required=True,
        default=lambda s: fields.Datetime.now(),
    )
    group_by = fields.Selection(
        selection=[
            ('none', 'No Grouping'),
            ('commercial', 'Carrier Commercial Partner'),
            ('carrier', 'Carrier Partner'),
            ('service', 'Carrier Service'),
        ],
        default='carrier',
        required=True,
        help='When creating purchase orders, this will be used to determine'
             ' the rates that go on each order.',
    )

    @api.multi
    def action_purchase(self):
        """ Purchase rate quotes """

        self.ensure_one()

        purchase_rates = defaultdict(self.env['stock.picking.rate'].browse)
        for rate in self.rate_ids:
            group_map = {
                'none': rate.id,
                'commercial': rate.partner_id.commercial_partner_id.id,
                'carrier': rate.partner_id.id,
                'service': rate.service_id.id,
            }
            po_id = group_map[self.group_by]
            purchase_rates[po_id] += rate
            rate.buy()

        purchase_orders = self.env['purchase.order']
        for rates in purchase_rates.values():
            purchase_orders += purchase_orders.create(
                self._get_purchase_order_vals(rates)
            )

        self.rate_ids._expire_other_rates()

        return self.action_show_purchases(purchase_orders)

    @api.multi
    def _get_purchase_line_vals(self, rate):
        """ Get values used for purchasing dispatch rates
        This will be useful for classes requiring custom purchase logic,
        such as external carrier connectors
        """
        return {
            'product_id': rate.service_id.product_id.id,
            'name': rate.display_name,
            'date_planned': self.date_po,
            'product_qty': 1,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'price_unit': rate.rate,
            'currency_id': rate.rate_currency_id.id,
            'reference': '%s,%d' % (rate._name, rate.id),
        }

    @api.multi
    def _get_purchase_order_vals(self, rate_ids):
        """ Get values for use in purchase order creation """
        self.ensure_one()
        if not len(rate_ids):
            return
        return {
            'partner_id': rate_ids[0].partner_id.id,
            'date_planned': self.date_po,
            'state': 'purchase',
            'order_line': [
                (0, 0, self._get_purchase_line_vals(r)) for r in rate_ids
            ]
        }
