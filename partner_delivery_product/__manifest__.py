# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Partner Delivery Product',
    'summary': 'Set on partners a product for delivery goods',
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'category': 'Delivery',
    'website': 'https://github.com/OCA/delivery-carrier',
    'author': 'PlanetaTIC, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'delivery',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
}
