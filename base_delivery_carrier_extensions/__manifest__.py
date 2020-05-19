# © 2020 FactorLibre - Zahra Velasco <zahra.velasco@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Base delivery carrier extension',
    'version': '11.0.1.0.0',
    'depends': [
        'delivery',
        'base_delivery_carrier_label'
    ],
    'category': 'Stock',
    'author': 'FactorLibre',
    'license': 'AGPL-3',
    'website': 'http://www.factorlibre.com',
    'data': [
        'views/stock_view.xml'
    ],
    'installable': True,
    'application': False
}
