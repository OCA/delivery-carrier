# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        return_pickings = self.filtered(
            lambda pick: pick.move_ids.origin_returned_move_id
        )
        # For returns, we deal with fee reimburse
        return_pickings._update_delivery_fee_on_return()
        (self - return_pickings)._add_delivery_fee_to_order()
        return res

    def _full_returned(self):
        full_returned = False
        for move in self.move_ids:
            full_returned = not float_compare(
                move.quantity_done,
                sum(
                    move.returned_move_ids.filtered(lambda x: x.state == "done").mapped(
                        "quantity_done"
                    )
                ),
                precision_rounding=move.product_uom.rounding,
            )
            if not full_returned:
                break
        return full_returned

    def _update_delivery_fee_on_return(self):
        """All pickings returned: we can refund the fee"""
        for sale in self.move_ids.origin_returned_move_id.picking_id.sale_id:
            if not sale.all_fee_pickings_returned:
                continue
            for fee_line in sale.order_line.filtered("is_delivery_fee"):
                carrier = fee_line.delivery_fee_picking_id.carrier_id
                # No fee refund for this carrier or already returned
                if not carrier.fee_return_percentage or fee_line.product_uom_qty < 1:
                    continue
                # We change the initial demand so the type of invoicing policy doesn't
                # affect in order to trigger the refund.
                fee_line.product_uom_qty = (
                    fee_line.product_uom_qty
                    - (fee_line.product_uom_qty * carrier.fee_return_percentage) / 100
                )

    def _add_delivery_fee_to_order(self):
        for picking in self:
            if (
                picking.picking_type_code != "outgoing"
                or not picking.sale_id
                or picking.partner_id.delivery_fee_exemption
                or not picking.carrier_id.fee_product_id
            ):
                continue
            # In the case we want to apply the fee just once
            if (
                picking.company_id.one_delivery_fee_by_sale_order
                and picking.sale_id.order_line.filtered("is_delivery_fee")
            ):
                continue
            picking.sale_id._create_delivery_fee_line(picking)
