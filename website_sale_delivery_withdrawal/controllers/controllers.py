# -*- coding: utf-8 -*-
import pytz


from odoo import http, _
from odoo.addons.website_sale.controllers.main import WebsiteSale, PaymentPortal
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery
from odoo.exceptions import AccessDenied, ValidationError, UserError
from odoo.tools.misc import get_lang, babel_locale_parse
from odoo.http import request
from datetime import datetime


class WithdrawalPoints(http.Controller):

    @http.route(['/website_sale_delivery_withdrawal/update_shipping'], type='json', auth="public", website=True)
    def withdrawal_update_shipping(self, **data):
        order = request.website.sale_get_order()
        commitment_date = datetime.strptime(data['commitment_date'], "%d/%m/%Y %H:%M")
        order.commitment_date = commitment_date
        order.picking_type_id = data['picking_type_id']
        if order.partner_id == request.website.user_id.sudo().partner_id:
            raise AccessDenied('Customer of the order cannot be the public user at this step.')

        partner_shipping = order.partner_id.sudo()._withdrawal_search_or_create({
            'name': data['city'],
            'street': data['street'],
            'zip': data['zip'],
            'city': data['city'],
            'country_id': data['country'],
        })
        if order.partner_shipping_id != partner_shipping:
            order.partner_shipping_id = partner_shipping
            order.onchange_partner_shipping_id()

        return {
            'address': request.env['ir.qweb']._render('website_sale.address_on_payment', {
                'order': order,
                'only_services': order and order.only_services,
            }),
            'new_partner_shipping_id': order.partner_shipping_id.id,
        }


class WebsiteSaleDeliveryMondialrelay(WebsiteSaleDelivery):

    def _update_website_sale_delivery_return(self, order, **post):
        res = super()._update_website_sale_delivery_return(order, **post)

        if order.carrier_id.is_withdrawal_point:
            res['withdrawal_point'] = {
                'allowed_points': order.carrier_id.withdrawal_point_ids.mapped('id'),
            }

        return res

