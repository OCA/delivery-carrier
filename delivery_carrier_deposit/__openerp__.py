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
    'version': '9.0.0.2.0',
    'category': 'Delivery',
    'author': "Akretion,Odoo Community Association (OCA)",
    'maintainer': 'Akretion',
    'summary': 'Create deposit slips',
    'depends': [
        'base_delivery_carrier_label',
    ],
    'website': 'https://www.akretion.com/',
    'data': [
        'views/stock_view.xml',
        'wizards/deposit.xml',
        'data/ir_sequence_data.xml',
        'report/report.xml',
        'report/deposit_slip.xml',
        'security/ir.model.access.csv',
        'security/model_security.xml',
    ],
    'demo': [],
    'installable': True,
    'license': 'AGPL-3',
}
