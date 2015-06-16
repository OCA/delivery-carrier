# -*- coding: utf-8 -*-
#
#
#    Authors: Guewen Baconnier
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#


from openerp import models, fields, api, exceptions, _


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    postlogistics_manual_cod_amount = fields.Float(
        string='Postlogistics Cash On Delivery Amount',
        help='If the cash on delivery amount for this package is different '
             'than the total of the sales order, write the amount there.'
    )

    @api.multi
    @api.returns('stock.picking')
    def _get_origin_pickings(self):
        self.ensure_one()
        operation_model = self.env['stock.pack.operation']
        operations = operation_model.search(
            [('result_package_id', '=', self.id)]
        )
        return operations.mapped('picking_id')

    @api.multi
    def postlogistics_cod_amount(self):
        """ Return the Postlogistic Cash on Delivery amount of a package

        If we have only 1 package which delivers the whole sales order
        we use the total amount of the sales order.

        Otherwise we don't know the value of each package so we raise an
        error and the user has to write the prices on the packages.

        When a price is manually set on a package, it's always used as the
        cash on delivery amount.
        """
        self.ensure_one()
        if self.postlogistics_manual_cod_amount:
            return self.postlogistics_manual_cod_amount

        pickings = self._get_origin_pickings()
        if len(pickings) > 1:
            raise exceptions.Warning(
                _('The cash on delivery amount must be manually specified '
                  'on the packages when a sales order is delivered '
                  'in several delivery orders.')
            )

        order = pickings.sale_id
        if not order:
            return 0.0
        if len(order) > 1:
            raise exceptions.Warning(
                _('The cash on delivery amount must be manually specified '
                  'on the packages when a package contains products '
                  'from different sales orders.')
            )

        order_moves = order.mapped('order_line.procurement_ids.move_ids')
        package_moves = self.mapped('quant_ids.history_ids')
        # check if the package delivers the whole sales order
        if order_moves != package_moves:
            raise exceptions.Warning(
                _('The cash on delivery amount must be manually specified '
                  'on the packages when a sales order is delivered '
                  'in several packages.')
            )

        return order.amount_total
