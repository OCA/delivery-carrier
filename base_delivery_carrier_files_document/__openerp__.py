# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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
    'name': 'Base module for picking carrier files creation for document',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse',
    'description': """
Allow to store the carrier files in a Document directory.
Auto-install when the module Document and
Base Delivery Carrier Files are installed.
    """,
    'author': 'Camptocamp',
    'license': 'AGPL-3',
    'website': 'http://www.camptocamp.com',
    'depends': ['base_delivery_carrier_files',
                'document'],
    'data': ['carrier_file_view.xml'],
    'demo': ['carrier_file_demo.xml'],
    'test': ['test/carrier_file.yml',
             'test/carrier_file_manual.yml'],
    'images': [],
    'installable': False,
    'auto_install': True,
}
