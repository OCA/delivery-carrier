# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _should_add_delivery_fee_to_order(self):
        # Keep fees on the paid shipment, not on the later deposit release.
        self.ensure_one()
        res = super()._should_add_delivery_fee_to_order()
        if self._is_full_customer_deposit_delivery():
            return False
        if self._is_customer_deposit_creation():
            carrier = self._get_delivery_fee_carrier()
            return not (
                not self.sale_id
                or self.partner_id.delivery_fee_exemption
                or not carrier.fee_product_id
            )
        return res

    def _get_delivery_fee_carrier(self):
        self.ensure_one()
        if self._is_customer_deposit_creation():
            return self.sale_id.carrier_id
        return super()._get_delivery_fee_carrier()

    def _is_customer_deposit_creation(self):
        """The first transfer to customer-owned stock is still a real delivery."""
        self.ensure_one()
        return (
            self.sale_id.customer_deposit
            and self.sale_id.warehouse_id.customer_deposit_type_id
            == self.picking_type_id
        )

    def _is_full_customer_deposit_delivery(self):
        """Only skip fees when the whole picking comes from the deposit route."""
        self.ensure_one()
        if self.sale_id.customer_deposit:
            return False
        deposit_deliveries = self.move_ids.filtered(
            lambda x: x.sale_line_id.route_id
            == x.sale_line_id.warehouse_id.customer_deposit_route_id
        )
        return bool(deposit_deliveries) and not (self.move_ids - deposit_deliveries)
