# -*- coding: utf-8 -*-
# © 2017 Angel Moya (PESOL)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{'name': 'Delivery Carrier Labels Direct Print',
 'version': '10.0.1.0.0',
 'author': "PESOL,Odoo Community Association (OCA)",
 'website': 'http://www.pesol.es',
 'category': 'Delivery',
 'depends': [
     'base_delivery_carrier_label',
     'base_report_to_printer'],
 'data': [
     'views/delivery.xml', ],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 }
