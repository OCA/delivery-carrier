# -*- coding: utf-8 -*-
# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Base Delivery Carrier Files',
    'version': '8.0.1.2.4',
    'category': 'Generic Modules/Warehouse',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'base',
        'stock',
        'delivery'
    ],
    'data': [
        'views/carrier_file_view.xml',
        'views/stock_view.xml',
        'wizards/generate_carrier_files_view.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [
        'demo/carrier_file_demo.xml',
        'demo/carrier_file_demo.yml'
    ],
    'test': [
        'test/carrier_file.yml',
        'test/carrier_file_manual.yml'
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
}
