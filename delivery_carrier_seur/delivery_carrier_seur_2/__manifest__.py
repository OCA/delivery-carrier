##############################################################################
#
#    Copyright (C) 2020-Today Trey, Kilobytes de Soluciones <www.trey.es>
#    Copyright (C) 2020-Today FactorLibre <www.factorlibre.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Delivery carrier SEUR',
    'summary': 'Integrate SEUR webservice',
    'author': 'Trey (www.trey.es), '
              'FactorLibre, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/delivery-carrier',
    'license': 'AGPL-3',
    'category': 'Delivery',
    'version': '12.0.1.0.0',
    'depends': [
        'delivery',
        'delivery_carrier_state',
        'stock_picking_delivery_info_computation',
    ],
    'external_dependencies': {
        'python': ['zeep'],
    },
    'data': [
        'views/delivery_carrier.xml',
    ],
}
