# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2019 Halltic eSolutions (http://halltic.com)
#                  Tristán Mozos <tristan.mozos@halltic.com>
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
{
    'name':'Delivery company management',
    'version':'0.1',
    'author':"Halltic eSolutions",
    'category':'Stock',
    'depends':[
        'delivery',
        'base_delivery_carrier_label',
        'delivery_carrier_mrw',
        'delivery_carrier_correos',
        'delivery_carrier_spring',
        'connector_amazon',
    ],
    'website':'https://halltic.com',
    'data':[
        'security/ir.model.access.csv',
        'view/mass_delivery_view.xml',
        'view/delivery_mass_shipment_menu.xml'
    ],
    'demo':[],
    'installable':True,
    'auto_install':False,
    'license':'AGPL-3',
}
