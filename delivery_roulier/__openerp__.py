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
        'base_phone',
        'document',
        'keychain',
        'base_suspend_security',
        # 'intrastat_product', # not ported yet, customs will not work
        'delivery_carrier_b2c',
    ],
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery.xml',
    ],
    'demo': [
        # 'demo/product.xml',
    ],
    'external_dependencies': {
        'python': [
            'roulier',  # 'git+https://github.com/akretion/roulier.git'
        ],
    },
    'tests': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
