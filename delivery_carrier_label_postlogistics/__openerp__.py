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
{'name': 'PostLogistics Labels WebService',
 'version': '8.0.1.1.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'version',
 'complexity': 'normal',
 'depends': ['base_delivery_carrier_label'],
 'website': 'http://www.camptocamp.com/',
 'data': ['res_partner_data.xml',
          'delivery_data.xml',
          'delivery_view.xml',
          'res_config_view.xml',
          'security/ir.model.access.csv',
          ],
 'tests': [],
 'installable': True,
 'auto_install': False,
 'application': True,
 'external_dependencies': {
     'python': ['suds'],
 }
 }
