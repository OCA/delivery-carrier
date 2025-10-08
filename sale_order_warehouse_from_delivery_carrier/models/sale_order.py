from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("user_id", "company_id", "carrier_id")
    def _compute_warehouse_id(self):
        # Set warehouse by shipping method
        so_with_shipping = self.browse()
        for order in self:
            if (
                order.state == "draft"
                and order.carrier_id
                and order.carrier_id.so_warehouse_id
            ):
                order.warehouse_id = order.carrier_id.so_warehouse_id
                so_with_shipping |= order
        return super(SaleOrder, self - so_with_shipping)._compute_warehouse_id()
