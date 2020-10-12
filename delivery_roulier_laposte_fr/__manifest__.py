# © 2017 Raphael REVERDY <raphael.reverdy@akretion.com>
#        David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Delivery Carrier La Poste (fr)',
    'version': '12.0.1.0.0',
    'author': 'Akretion',
    'summary': 'Generate Label for La Poste/Colissimo',
    'maintainer': 'Akretion,Odoo Community Association (OCA)',
    'category': 'Warehouse',
    'depends': [
        'delivery_roulier_option',
        'intrastat_base',  # for customs declaration
    ],
    'data': [
        'data/delivery.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
