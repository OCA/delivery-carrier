# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def _get_partner_delivery_product(self, order):
        return order.partner_id.delivery_product_id

    def fixed_rate_shipment(self, order):
        product = self._get_partner_delivery_product(order)

        if not product:
            return super(DeliveryCarrier, self).fixed_rate_shipment(order)

        carrier = self._match_address(order.partner_shipping_id)
        if not carrier:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error: this delivery method is not '
                                       'available for this address.'),
                    'warning_message': False}
        price = product.list_price
        if (self.company_id and
                self.company_id.currency_id.id != order.currency_id.id):
            price = self.env['res.currency']._compute(
                self.company_id.currency_id, order.currency_id, price)
        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': False}
