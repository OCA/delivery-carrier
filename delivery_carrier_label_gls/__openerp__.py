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
    'name': 'Delivery Carrier Label GLS',
    'version': '0.1',
    'author': 'Akretion',
    'maintener': 'Akretion',
    'category': 'Warehouse',
    'summary': "GLS carrier label printing",
    'depends': [
        'base_delivery_carrier_label',
        'configuration_helper',
        'partner_helper',
    ],
    'description': """
Delivery Carrier Label GLS (french carrier)
=============================================

GLS carrier https://gls-group.eu/


Contributors
------------
* David BEAL <david.beal@akretion.com>

""",
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery_carrier.xml',
        'data/sequence.xml',
        'config_view.xml',
        # 'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/res.partner.csv',
        'demo/company.xml',
        'demo/product.xml',
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
