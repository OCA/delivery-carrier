# -*- coding: utf-8 -*-
# © 2020 FactorLibre - Zahra Velasco <zahra.velasco@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    date_shipped = fields.Date('Shipment Date', readonly=True)
    date_delivered = fields.Datetime('Delivery Date', readonly=True)
    tracking_status = fields.Char('Tracking status', readonly=True, index=True)
    tracking_status_history = fields.Text(
        'Tracking status history',
        readonly=True)
    carrier_status_picking = fields.Selection([
        ('shipping_recorded_in_carrier', 'shipping recorded in carrier'),
        ('in_transit', 'In transit'),
        ('canceled_shipment', 'Canceled shipment'),
        ('incidence', 'incidence'),
        ('customer_delivered', 'Customer delivered'),
        ('warehouse_delivered', 'Warehouse delivered')
    ], string="Carrier State", readonly=True)

    @api.multi
    def carrier_tracking_status(self):
        pass

    @api.multi
    def carrier_delivery_create(self):
        self.ensure_one()
        self.carrier_status_picking = 'shipping_recorded_in_carrier'

    @api.multi
    def carrier_delivery_cancel(self):
        self.ensure_one()
        self.carrier_status_picking = 'canceled_shipment'
