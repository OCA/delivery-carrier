# -*- coding: utf-8 -*-
# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Base module for picking carrier files creation for document',
    'version': '8.0.1.0.1',
    'category': 'Generic Modules/Warehouse',
    'author': 'Camptocamp,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'base_delivery_carrier_files',
        'document'
    ],
    'data': [
        'views/carrier_file_view.xml'
    ],
    'demo': [
        'demo/carrier_file_demo.xml'
    ],
    'images': [],
    'installable': True,
    'auto_install': True,
}
