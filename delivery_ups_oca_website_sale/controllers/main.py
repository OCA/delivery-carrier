# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.http import request

from odoo.addons.website_sale.controllers.delivery import Delivery


class UpsGlobalCheckoutDelivery(Delivery):
    def _order_summary_values(self, order, **kwargs):
        res = super()._order_summary_values(order, **kwargs)
        landed_cost = sum(
            order.order_line.filtered("is_ups_landed_cost").mapped("price_total")
        )
        monetary = request.env["ir.qweb.field.monetary"]
        res["ups_landed_cost"] = (
            monetary.value_to_html(landed_cost, {"display_currency": order.currency_id})
            if landed_cost
            else ""
        )
        return res
