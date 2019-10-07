# -*- coding: utf-8 -*-
#    Author: David BEAL <david.beal@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Delivery Deposit',
    'version': '10.0.0.1.1',
    'category': 'Delivery',
    'author': "Akretion,Odoo Community Association (OCA)",
    'maintainer': 'Akretion',
    'summary': 'Create deposit slips',
    'depends': [
        'base_delivery_carrier_label',
    ],
    'website': 'https://github.com/OCA/delivery-carrier',
    'data': [
        'views/mass_delivery_view.xml',
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
