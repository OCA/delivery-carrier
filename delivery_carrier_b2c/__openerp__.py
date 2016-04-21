# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Chafique DELLI <chafique.delli@akretion.com>
#    Copyright 2014 Akretion
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
    'name': 'Delivery Carrier Business To Customer',
    'version': '8.0.0.2.0',
    'author': "Akretion,Odoo Community Association (OCA)",
    'maintainer': 'Akretion',
    'category': '',
    'depends': [
        'base_delivery_carrier_label',
        'partner_helper',
    ],
    'website': 'http://www.akretion.com/',
    'data': [
        'partner_view.xml',
    ],
    'tests': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
