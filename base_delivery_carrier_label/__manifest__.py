# Copyright 2013-2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{'name': 'Base module for carrier labels',
 'version': '12.0.2.0.0',
 'author': "Camptocamp,Akretion,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Delivery',
 'depends': ['delivery'],
 'website': 'https://github.com/OCA/delivery-carrier',
 'data': [
     'views/delivery.xml',
     'views/stock.xml',
     'views/res_config.xml',
     'views/carrier_account.xml',
     'security/ir.model.access.csv',
     'security/carrier_security.xml',
     'wizard/manifest_wizard_view.xml',
 ],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 }
