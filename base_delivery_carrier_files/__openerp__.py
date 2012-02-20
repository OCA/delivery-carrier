# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (c) 2012 Camptocamp SA (http://www.camptocamp.com)
#   @author Guewen Baconnier
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    'name': 'Base Delivery Carrier Files',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse',
    'description': """
Base module for creation of carrier files  (La Poste, TNT Express Shipper, ...). exported as text (csv, ...).
It contains the base structure to handle the export of files on Delivery Orders and an API to ease the generation of the files for the developers in sub-modules.

The delivery orders can be grouped in one files or be exported each one in a separate file.
The files can be generated automatically on the shipment of a Delivery Order or from a manual action.
They are exported to a defined path or in a document directory of your choice if the "document" module is installed.

A generic carrier file is included in the module. It can also be used as a basis to create your own sub-module.

Sub-modules already exist to generate file according to specs of :
 - La Poste (France) : delivery_carrier_file_laposte
 - TNT Express Shipper (France) : delivery_carrier_file_tnt
 - Make your own ! Look at the code of the modules above, it's trivial to create a sub-module for a carrier.

""",
    'author': 'Camptocamp',
    'website': 'http://www.camptocamp.com',
    'depends': ['base',
                'stock',
                'delivery'],
    'init_xml': [],
    'update_xml': ['carrier_file_view.xml',
                   'stock_view.xml',
                   'wizard/generate_carrier_files_view.xml',
                   'security/ir.model.access.csv'],
    'demo_xml': ['carrier_file_demo.xml',
                 'carrier_file_demo.yml'],
    'test': ['test/carrier_file.yml',
             'test/carrier_file_manual.yml'],
    'images': [],
    'installable': True,
    'auto_install': False,
}
