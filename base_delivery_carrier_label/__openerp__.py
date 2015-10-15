# -*- coding: utf-8 -*-
# © 2013-2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{'name': 'Base module for carrier labels',
 'version': '9.0.1.0.0',
 'author': "Camptocamp,Akretion,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Delivery',
 'complexity': 'normal',
 'depends': ['delivery'],
 'website': 'http://www.camptocamp.com/',
 'data': [
     'views/delivery.xml',
     'views/stock.xml',
     'views/res_config.xml',
     'security/ir.model.access.csv',
 ],
 'tests': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 }
