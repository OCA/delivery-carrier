# © 2016 Raphael REVERDY <raphael.reverdy@akretion.com>
#        David BEAL <david.beal@akretion.com>
#        Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Delivery Roulier Option',
    'version': '12.0.1.0.0',
    'author': 'Akretion',
    'summary': 'Add options to roulier modules',
    'maintainer': 'Akretion, Odoo Community Association (OCA)',
    'category': 'Warehouse',
    'depends': [
        'delivery_roulier',
        'product_harmonized_system',  # from oca/intrastat
    ],
    'website': 'https://github.com/OCA/delivery-carrier',
    'data': [
        'data/delivery.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
