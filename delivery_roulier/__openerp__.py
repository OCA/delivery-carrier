# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Delivery Carrier Roulier',
    'version': '9.0.1.0.0',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'summary': 'Integration of multiple carriers',
    'maintainer': 'Akretion, Odoo Community Association (OCA)',
    'category': 'Warehouse',
    'depends': [
        'partner_helper',
        'base_phone',  # from oca/telephony
        'keychain',  # from oca/server-tools
        'base_suspend_security',
        'product_harmonized_system',  # from oca/intrastat
        'base_delivery_carrier_label',
        'delivery_carrier_deposit',
    ],
    'website': 'http://www.akretion.com/',
    'data': [
        'views/stock_quant_package.xml',
    ],
    'external_dependencies': {
        'python': [
            'roulier',  # '>0.1.4'
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
