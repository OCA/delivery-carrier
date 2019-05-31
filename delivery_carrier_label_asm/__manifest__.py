# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 2014 Akretion
#    @author David BEAL <david.beal@akretion.com>
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
###############################################################################


{
    'name': 'Delivery Carrier Label ASM',
    'version': '12.0.1.0.0',
    'author': "Akretion,"
              "PESOL,"
              "Odoo Community Association (OCA)",
    'maintener': 'Akretion',
    'category': 'Warehouse',
    'summary': "ASM carrier label printing",
    'depends': [
        'base_delivery_carrier_label'
    ],
    'website': 'http://www.akretion.com/ http://www.pesol.es',
    'data': [
        'data/delivery_carrier.xml',
        'data/sequence.xml',
        'views/picking_view.xml',
    ],
    'external_dependencies': {
        'python': [
            'pycountry',
            'unidecode',
        ],
    },
    'license': 'AGPL-3',
    'tests': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
