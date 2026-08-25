from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_order_lines_to_report(self):
        lines = super()._get_order_lines_to_report()
        return lines.filtered(
            lambda line: not line.is_free_delivery
            or (
                line.is_free_delivery
                and not line.company_id.report_saleorder_hide_free_delivery_lines
            )
        )
