# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: David BEAL
#    Copyright 2014 Akretion
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
    'name': 'Delivery Deposit',
    'version': '0.2',
    'category': 'Warehouse',
    'author': 'Akretion',
    'maintainer': 'Akretion',
    'depends': [
        'base_delivery_carrier_label',
    ],
    'description': """
Description
-----------
Allows to gather all delivery orders by 'delivery method'
and date delivery in 'Deposit slip' model.

Provides a report which summarizes all deliveries for each carrier.

How to use
----------
- generate report deliveries with the menu 'warehouse / create deposit slip'
- print it

Contributors
------------
* David BEAL <david.beal@akretion.com>
* Sébastien BEAU <sebastien.beau@akretion.com>
* Benoit GUILLOT <benoit.guillot@akretion.com>
* Chafique DELLI <chafique.delli@akretion.com>
""",
    'website': 'http://www.akretion.com/',
    'data': [
        'stock_view.xml',
        'wizard/deposit.xml',
        'ir_sequence_data.xml',
        'report/report.xml',
        'report/deposit_slip.xml',
        'security/ir.model.access.csv',
        ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
