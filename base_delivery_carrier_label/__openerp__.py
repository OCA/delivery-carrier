# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{'name': 'Base module for carrier labels',
 'version': '8.0.1.2.0',
 'author': "Camptocamp,Akretion,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Delivery',
 'complexity': 'normal',
 'depends': ['delivery'],
 'website': 'http://www.camptocamp.com/',
 'data': ['delivery_view.xml',
          'stock_view.xml',
          'res_config_view.xml',
          'security/ir.model.access.csv',
          ],
 'tests': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': True,
 }
