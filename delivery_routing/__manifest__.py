# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Routing',
    'version': '13.0.1.0.0',
    'author': 'Camptocamp',
    'license': 'AGPL-3',
    'category': 'Inventory',
    'website': 'http://www.camptocamp.ch',
    'images': [],
    'depends': [
        'base',
        'base_geolocalize',
        'stock',
    ],
    'data': [
        'views/stock_menu_views.xml',
        'views/res_partner.xml',
        'wizard/routing_wizard.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['routing-ortools-osrm==1.0.1'],
    },
}
