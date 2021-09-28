# -*- coding: utf-8 -*-
{
    'name': 'Delivery Carrier File: TNT',
    'version': '10.0.1.0.1',
    'category': 'Generic Modules/Warehouse',
    'summary': """
Sub-module for Base Delivery Carrier Files.

Definition of the delivery carrier file for "TNT Express Shipper".
    """,
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'base_delivery_carrier_files'
    ],
    'data': [
        'views/delivery_carrier_file.xml'
    ],
    'installable': True,
    'auto_install': False,
}
