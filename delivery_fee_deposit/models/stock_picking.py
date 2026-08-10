# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _should_add_delivery_fee_to_order(self):
        # Keep fees on the paid shipment, not on the later deposit release.
        self.ensure_one()
        res = super()._should_add_delivery_fee_to_order()
        if self._delivery_fee_deposit_is_full_delivery():
            return False
        if self._delivery_fee_deposit_is_creation():
            carrier = self._get_delivery_fee_carrier()
            return not (
                not self.sale_id
                or self.partner_id.delivery_fee_exemption
                or not carrier.fee_product_id
            )
        if self._delivery_fee_deposit_is_mixed_delivery():
            carrier = self._get_delivery_fee_carrier()
            return not (
                self.picking_type_code != "outgoing"
                or not self.sale_id
                or self.partner_id.delivery_fee_exemption
                or not carrier.fee_product_id
            )
        return res

    def _get_delivery_fee_carrier(self):
        self.ensure_one()
        if not self.carrier_id and (
            self._delivery_fee_deposit_is_creation()
            or self._delivery_fee_deposit_is_mixed_delivery()
        ):
            return self.sale_id.carrier_id
        return super()._get_delivery_fee_carrier()

    def _full_returned_for_delivery_fee(self):
        self.ensure_one()
        if not self._delivery_fee_deposit_is_mixed_delivery():
            return super()._full_returned_for_delivery_fee()
        return all(
            self._delivery_fee_deposit_move_full_returned(move)
            for move in self.move_ids - self._delivery_fee_deposit_moves()
        )

    def _should_update_delivery_fee_on_return(self, sale, fee_line):
        fee_picking = fee_line.delivery_fee_picking_id
        if (
            fee_picking._delivery_fee_deposit_is_creation()
            or fee_picking._delivery_fee_deposit_is_mixed_delivery()
        ):
            return fee_picking._full_returned_for_delivery_fee()
        return super()._should_update_delivery_fee_on_return(sale, fee_line)

    def _delivery_fee_deposit_is_creation(self):
        """The first transfer to customer-owned stock is still a delivery."""
        self.ensure_one()
        return (
            self.sale_id.customer_deposit
            and self.sale_id.warehouse_id.customer_deposit_type_id
            == self.picking_type_id
        )

    def _delivery_fee_deposit_is_full_delivery(self):
        """Only skip fees when the whole picking releases customer-owned stock."""
        self.ensure_one()
        if self.sale_id.customer_deposit:
            return False
        deposit_deliveries = self._delivery_fee_deposit_moves()
        return bool(deposit_deliveries) and not (self.move_ids - deposit_deliveries)

    def _delivery_fee_deposit_is_mixed_delivery(self):
        self.ensure_one()
        if self.sale_id.customer_deposit:
            return False
        deposit_deliveries = self._delivery_fee_deposit_moves()
        return bool(deposit_deliveries) and bool(self.move_ids - deposit_deliveries)

    def _delivery_fee_deposit_moves(self):
        self.ensure_one()
        return self.move_ids.filtered(
            lambda move: self._delivery_fee_deposit_is_move(move)
        )

    def _delivery_fee_deposit_move_full_returned(self, move):
        return not float_compare(
            move.quantity,
            sum(
                move.returned_move_ids.filtered(
                    lambda returned_move: returned_move.state == "done"
                ).mapped("quantity")
            ),
            precision_rounding=move.product_uom.rounding,
        )

    def _delivery_fee_deposit_is_move(self, move):
        partner = move.sale_line_id.order_id.partner_id.commercial_partner_id
        if not partner or not move.move_line_ids:
            return False
        return all(
            line.owner_id and line.owner_id.commercial_partner_id == partner
            for line in move.move_line_ids
        )
