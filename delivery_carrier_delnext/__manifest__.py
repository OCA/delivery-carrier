# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Halltic eSolutions (http://www.halltic.com)
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
    'name':'Delnext Deliveries',
    'version':'0.1',
    'author':"Halltic",
    'category':'Sales Management',
    'depends':[
        'delivery',
        'base_delivery_carrier_label'
    ],
    'website':'http://www.halltic.com',
    'data':[
        # 'security/ir.model.access.csv',
        'view/delnext_config_view.xml',
        'view/delivery_view.xml',
        'view/mass_delivery_view.xml'
    ],
    'demo':[],
    'installable':True,
    'auto_install':False,
    'license':'AGPL-3',
}
