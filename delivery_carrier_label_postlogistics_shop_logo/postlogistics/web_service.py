# -*- coding: utf-8 -*-
# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from PIL import Image
from StringIO import StringIO

from odoo.addons.delivery_carrier_label_postlogistics.postlogistics import (
    web_service
)


class PostlogisticsWebServiceShop(web_service.PostlogisticsWebService):

    """ Use picking information to get shop logo """

    def _get_shop_label_logo(self, picking):
        shop_logo = {}
        shop = picking.sale_id.shop_id
        if shop and shop.postlogistics_logo:
            logo = shop.postlogistics_logo
            logo_image = Image.open(StringIO(logo.decode('base64')))
            logo_format = logo_image.format
            shop_logo['Logo'] = logo
            shop_logo['LogoFormat'] = logo_format
        return shop_logo

    def _prepare_envelope(self, picking, post_customer, data):
        """ Replace company label logo by shop label logo in customer data """
        shop_logo = self._get_shop_label_logo(picking)
        post_customer.update(shop_logo)
        return super(PostlogisticsWebServiceShop, self
                     )._prepare_envelope(picking, post_customer, data)
