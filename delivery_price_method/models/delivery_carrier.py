# Copyright 2020 Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    # You must add next method to your carrier model if want use this price
    # method
    #
    # def [CARRIER]_rate_shipment(self, order):
    #     return self.price_method_rate_shipment(order)

    price_method = fields.Selection(
        selection=[
            ('fixed', 'Fixed price'),
            ('base_on_rule', 'Based on Rules'),
        ],
        string='Price method',
        default='fixed',
    )

    def price_method_rate_shipment(self, order):
        return getattr(self, '%s_rate_shipment' % self.price_method)(order)

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        rates = getattr(self, '%s_send_shipping' % self.price_method)(pickings)
        for index, rate in enumerate(rates):
            res[index]['exact_price'] = rate['exact_price']
        return res
