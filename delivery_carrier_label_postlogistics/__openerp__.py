# -*- coding: utf-8 -*-
# © 2013-2016 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{'name': 'PostLogistics Labels WebService',
 'version': '9.0.1.1.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Delivery',
 'complexity': 'normal',
 'depends': ['base_delivery_carrier_label',
             'configuration_helper'],
 'website': 'http://www.camptocamp.com/',
 'data': ['data/res_partner.xml',
          'data/delivery.xml',
          'views/delivery.xml',
          'views/postlogistics_license.xml',
          'views/res_config.xml',
          'views/stock.xml',
          'security/ir.model.access.csv',
          ],
 'installable': True,
 'auto_install': False,
 'application': True,
 'external_dependencies': {
     'python': ['suds'],
 }
 }
