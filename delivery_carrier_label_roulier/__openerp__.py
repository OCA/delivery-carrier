# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#
##############################################################################
{
    'name': 'Delivery Carrier Roulier',
    'version': '0.3',
    'author': 'Akretion',
    'summary': 'Integration of multiple carriers (base)',
    'maintainer': 'Akretion',
    'category': 'Warehouse',
    'depends': [
        'partner_helper',
        'delivery_carrier_b2c',
    ],
    'description': "",
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery.xml',
        # 'stock_view.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': [
            'roulier'  # 'git+https://github.com/akretion/roulier.git'
        ],
    },
    'tests': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
