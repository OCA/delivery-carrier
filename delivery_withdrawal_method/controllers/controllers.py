# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.addons.website_sale.controllers.main import WebsiteSale, PaymentPortal
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery

from odoo.exceptions import AccessDenied, ValidationError, UserError
from odoo.http import request



class WebsiteSaleDeliveryMondialrelay(WebsiteSaleDelivery):

    def _update_website_sale_delivery_return(self, order, **post):
        res = super()._update_website_sale_delivery_return(order, **post)
        if order.carrier_id.is_withdrawal_point:
            res['withdrawal_point'] = {
                'allowed_points': ','.join(order.carrier_id.withdrawal_point_ids.mapped('partner_id.city')).upper(),
            }
        return res
