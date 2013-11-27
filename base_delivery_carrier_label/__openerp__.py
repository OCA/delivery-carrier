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
 'version': '1.0',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'version',
 'complexity': 'normal',
 'depends': ['stock', 'delivery'],
 'description': """
Base module for carrier labels
==============================

This module adds a button on delivery orders to generate a label as an
attachement.

.. tip::
   It doesn't implement a label. To add a default label, you can install
   the module `delivery_carrier_label_default_webkit`

It can be used to print specific labels per carrier.

.. note::
   Inspired by Akretion module delivery_base and delivery_shipping_label

Contributors
------------

* David BEAL <david.beal@akretion.com>
* Sébastien BEAU <sebastien.beau@akretion.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>

 """,
 'website': 'http://www.camptocamp.com/',
 'data': [
     'delivery_view.xml',
     'stock_view.xml',
     ],
 'tests': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': True}
