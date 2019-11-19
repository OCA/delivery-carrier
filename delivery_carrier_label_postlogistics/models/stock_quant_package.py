# Copyright 2015-2019 Guewen Baconnier (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


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
