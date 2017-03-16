# coding: utf-8
# @author Raphael Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Delivery Carrier Roulier',
    'version': '9.0.0.0.0',
    'author': 'Akretion',
    'summary': 'Integration of multiple carriers (base)',
    'maintainer': 'Akretion, Odoo Community Association (OCA)',
    'category': 'Warehouse',
    'depends': [
        'partner_helper',
        'base_phone',  # from oca/telephony
        'document',
        'keychain',  # from oca/server-tools
        'base_suspend_security',
        'product_harmonized_system',  # from oca/intrastat
        'delivery_carrier_b2c',
    ],
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery.xml',
        'views/stock_quant_package.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': [
            'roulier',  # '>0.2'
        ],
    },
    'tests': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
