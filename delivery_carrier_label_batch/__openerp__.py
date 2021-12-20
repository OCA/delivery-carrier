# -*- coding: utf-8 -*-
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    'name': 'Carrier labels - Stock Batch Picking (link)',
    'version': '9.0.1.0.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'category': 'Carrier',
    'complexity': 'normal',
    'depends': ['base_delivery_carrier_label', 'stock_batch_picking'],
    'website': 'http://www.camptocamp.com/',
    'data': [
        'views/stock_batch_picking.xml',
        'wizard/generate_labels_view.xml',
        'wizard/apply_carrier_view.xml',
    ],
    'tests': [],
    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
    'application': False,
    'external_dependencies': {
        'python': ['PyPDF2'],
    }
}
