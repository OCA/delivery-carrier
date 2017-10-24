# -*- coding: utf-8 -*-
# Copyright 2016-2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Stock Picking Delivery',
    'summary': 'Adds the concept of shipment container packing and '
               'subsequent delivery from a stock picking.',
    'version': '10.0.1.0.0',
    'category': 'Extra Tools',
    'website': 'https://laslabs.com/',
    'author': 'LasLabs, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'base_locale_uom_default',
        'stock_picking_delivery_rate',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'views/stock_picking_view.xml',
        'wizards/stock_picking_delivery_view.xml',
    ],
}
