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
{
    'name': 'Carrier labels - Picking dispatch (link)',
    'version': '1.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'maintainer': 'Camptocamp',
    'category': 'version',
    'complexity': 'normal',
    'depends': ['base_delivery_carrier_label', 'picking_dispatch'],
    'description': """
[Link module] Carrier labels - Picking dispatch
==============================

This module adds a wizard on picking dispatch to generate the labels
of the packs. The labels are merged in one PDF file.

If you want multiple labels for one picking, all the moves should have been
put in a pack before the labels can be printed.

If you don't define your pack it will be considered a picking is a single pack.

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>

""",
    'website': 'http://www.camptocamp.com/',
    'data': [
        'picking_dispatch_view.xml',
        'wizard/generate_labels_view.xml',
        'wizard/apply_carrier_view.xml',
    ],
    'tests': [],
    'installable': False,
    'auto_install': True,
    'license': 'AGPL-3',
    'application': False,
    'external_dependencies': {
        'python': ['PyPDF2'],
    }
}
