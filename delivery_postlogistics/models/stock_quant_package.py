# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    postlogistics_manual_cod_amount = fields.Float(
        string="PostLogistics Cash On Delivery Amount",
        help="If the cash on delivery amount for this package is different "
        "than the total of the sales order, write the amount there.",
    )
    parcel_tracking = fields.Char("Parcel Tracking")
    package_carrier_type = fields.Selection(related="packaging_id.package_carrier_type")

    @api.returns("stock.picking")
    def _get_origin_pickings(self):
        self.ensure_one()
        move_line_model = self.env["stock.move.line"]
        move_line = move_line_model.search([("package_id", "=", self.id)])
        return move_line.mapped("picking_id")

    def postlogistics_cod_amount(self):
        """ Return the PostLogistics Cash on Delivery amount of a package

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
                _(
                    "The cash on delivery amount must be manually specified "
                    "on the packages when a sales order is delivered "
                    "in several delivery orders."
                )
            )

        order = pickings.sale_id
        if not order:
            return 0.0
        if len(order) > 1:
            raise exceptions.Warning(
                _(
                    "The cash on delivery amount must be manually specified "
                    "on the packages when a package contains products "
                    "from different sales orders."
                )
            )

        order_moves = order.mapped("order_line.procurement_ids.move_ids")
        package_moves = self.mapped("quant_ids.history_ids")
        # check if the package delivers the whole sales order
        if order_moves != package_moves:
            raise exceptions.Warning(
                _(
                    "The cash on delivery amount must be manually specified "
                    "on the packages when a sales order is delivered "
                    "in several packages."
                )
            )

        return order.amount_total
