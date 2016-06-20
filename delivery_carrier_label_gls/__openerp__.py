# coding: utf-8
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Delivery Carrier Label GLS',
    'version': '0.1',
    'author': "Akretion,Odoo Community Association (OCA)",
    'maintener': 'Akretion',
    'category': 'Warehouse',
    'summary': "GLS carrier label printing",
    'depends': [
        'base_delivery_carrier_label',
        'partner_helper',
    ],
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery_carrier.xml',
        'data/sequence.xml',
        'views/config_view.xml',
        'views/stock_view.xml',
    ],
    'demo': [
        'demo/res.partner.csv',
        'demo/company.xml',
        'demo/product.xml',
    ],
    'external_dependencies': {
        'python': [
            'pycountry',
            'unidecode',
        ],
    },
    'license': 'AGPL-3',
    'tests': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
