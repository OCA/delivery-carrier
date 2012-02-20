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
    'name': 'Base module for picking carrier files creation for document',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse',
    'description': """
Allow to store the carrier files in a Document directory.
Auto-install when the module Document and Base Delivery Carrier Files are installed.
    """,
    'author': 'Camptocamp',
    'website': 'http://www.camptocamp.com',
    'depends': ['base_delivery_carrier_files',
                'document'],
    'init_xml': [],
    'update_xml': ['carrier_file_view.xml',],
    'demo_xml': ['carrier_file_demo.xml'],
    'test': ['test/carrier_file.yml',
             'test/carrier_file_manual.yml',],
    'images': [],
    'installable': True,
    'auto_install': True,
}
