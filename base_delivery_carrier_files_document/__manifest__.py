# -*- coding: utf-8 -*-
# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Base module for picking carrier files creation for document',
    'version': '10.0.1.0.0',
    'category': 'Generic Modules/Warehouse',
    'summary': """
Allow to store the carrier files in a Document directory.
Auto-install when the module Document and
Base Delivery Carrier Files are installed.
    """,
    'author': "Camptocamp,Odoo Community Association (OCA)",
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
