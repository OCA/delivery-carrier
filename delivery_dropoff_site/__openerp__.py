# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 2014 Akretion
#    @author David BEAL <david.beal@akretion.com>
#            Aymeric LECOMTE
#            Sébastien BEAU <sebastien.beau@akretion.com>
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
###############################################################################

{
    'name': 'Delivery Drop-off Site',
    'version': '0.3',
    'author': 'Akretion',
    'summary': "Send goods to sites in which customers comes pick up package",
    'maintener': 'Akretion',
    'category': 'Warehouse',
    'depends': [
        'base_delivery_carrier_label',
        'file_document',
        'file_repository',
    ],
    'description': """
Delivery Drop-off Site
======================

Manage features related to drop-off sites
-----------------------------------------

Main international carriers provide transportation services to specific areas managed by them or by subcontractors.

Then, recipients comes pick up their packages in these sites


Contributors
------------

* David BEAL <david.beal@akretion.com>
* Aymeric LECOMTE, akretion
* Sébastien BEAU <sebastien.beau@akretion.com>

""",
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery_data.xml',
        'stock_view.xml',
        'partner_view.xml',
        #'security/ir.model.access.csv',
    ],
    'license': 'AGPL-3',
    'tests': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
