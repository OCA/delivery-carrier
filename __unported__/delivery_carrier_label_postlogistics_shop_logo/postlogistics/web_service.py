# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from PIL import Image
from StringIO import StringIO

from openerp.addons.delivery_carrier_label_postlogistics.postlogistics import (
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
