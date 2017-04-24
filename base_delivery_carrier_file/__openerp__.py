# -*- coding: utf-8 -*-
# © 2012 Guewen Baconnier (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Base Delivery Carrier Files',
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/Warehouse',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com',
    'depends': ['base',
                'stock',
                'delivery'],
    'data': ['views/carrier_file_view.xml',
             'views/stock_view.xml',
             'wizard/generate_carrier_files_view.xml',
             'security/ir.model.access.csv'],
    'demo': ['demo/carrier_file_demo.xml',
             'demo/carrier_file_demo.yml'],
    'test': ['test/carrier_file.yml',
             'test/carrier_file_manual.yml'],
    'installable': True,
}
