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
from openerp.osv import orm

from postlogistics.web_service import PostlogisticsWebServiceShop


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def _generate_postlogistics_label(self, cr, uid, picking,
                                      webservice_class=None, context=None):
        """ Generate post label using shop label """
        if webservice_class is None:
            webservice_class = PostlogisticsWebServiceShop
        return super(stock_picking, self)._generate_postlogistics_label(
            cr, uid, picking,
            webservice_class=webservice_class,
            context=context)
