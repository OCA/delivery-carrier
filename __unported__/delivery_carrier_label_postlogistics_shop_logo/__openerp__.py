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
{'name': 'PostLogistics labels - logo per Shop',
 'version': '1.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'version',
 'complexity': 'normal',
 'depends': ['delivery_carrier_label_postlogistics'],
 'description': """
PostLogistics labels - logo per Shop
====================================

Allow to set a custom logo per shop on PostLogistics labels.

Adds an image field on shop form to set it.
This permits to replace the Logo printed on PostLogistics sender labels.

If no shop logo is defined it still uses PostLogistics label logo
define on company.

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>

""",
 'website': 'http://www.camptocamp.com/',
 'license': 'AGPL-3',
 'data': ['sale_view.xml'],
 'test': [],
 'installable': False,
 'auto_install': False,
 'application': True,
 }
