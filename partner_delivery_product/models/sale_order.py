# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_delivery_line_description(self, carrier, product):
        carrier = carrier.with_context(lang=self.partner_id.lang)
        product = product.with_context(lang=self.partner_id.lang)
        return '%s: %s' % (carrier.name, product.name)

    def _create_delivery_line(self, carrier, price_unit):
        SaleOrderLine = self.env['sale.order.line']

        product = carrier._get_partner_delivery_product(self)
        if not product:
            return super(SaleOrder, self)._create_delivery_line(
                carrier, price_unit)

        # Apply fiscal position
        taxes = product.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(
                taxes, product, self.partner_id).ids

        # Create the sales order line
        description = self._get_delivery_line_description(carrier, product)
        values = {
            'order_id': self.id,
            'name': description,
            'product_uom_qty': 1,
            'product_uom': product.uom_id.id,
            'product_id': product.id,
            'price_unit': price_unit,
            'tax_id': [(6, 0, taxes_ids)],
            'is_delivery': True,
        }
        if self.order_line:
            values['sequence'] = self.order_line[-1].sequence + 1
        sol = SaleOrderLine.sudo().create(values)
        return sol
