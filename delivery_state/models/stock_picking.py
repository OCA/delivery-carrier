# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    date_shipped = fields.Date(
        string='Shipment Date',
        readonly=True,
    )
    date_delivered = fields.Datetime(
        string='Delivery Date',
        readonly=True,
    )
    tracking_state = fields.Char(
        string='Tracking state',
        readonly=True,
        index=True,
        track_visibility='always',
    )
    tracking_state_history = fields.Text(
        string='Tracking state history',
        readonly=True,
    )
    delivery_state = fields.Selection(
        selection=[
            ('shipping_recorded_in_carrier', 'Shipping recorded in carrier'),
            ('in_transit', 'In transit'),
            ('canceled_shipment', 'Canceled shipment'),
            ('incidence', 'Incidence'),
            ('customer_delivered', 'Customer delivered'),
            ('warehouse_delivered', 'Warehouse delivered'),
        ],
        string='Carrier State',
        track_visibility='onchange',
        readonly=True,
    )

    def tracking_state_update(self):
        for picking in self.filtered(lambda p: p.delivery_type):
            method = '%s_tracking_state_update' % picking.delivery_type
            if hasattr(picking.carrier_id, method):
                getattr(picking.carrier_id, method)(picking)
