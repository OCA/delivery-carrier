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

import csv

from openerp.addons.base_delivery_carrier_files.generator import CarrierFileGenerator
from openerp.addons.base_delivery_carrier_files.generator import BaseLine
from openerp.addons.base_delivery_carrier_files.csv_writer import UnicodeWriter


class LaPosteLine(BaseLine):
    fields = ('reference',
              'firstname',
              'lastname',
              'company_name',
              'street1',
              'street2',
              'street3',
              'street4',
              'zip',
              'city',
              'country_code',
              'phone',
              '',
              '',
              '',
              '',
              '',
              '',
              '',
              '',
              'weight')


class LaPosteFileGenerator(CarrierFileGenerator):

    @classmethod
    def carrier_for(cls, carrier_name):
        return carrier_name == 'la_poste'

    def _get_filename_single(self, picking, configuration, extension='csv'):
        return super(LaPosteFileGenerator, self)._get_filename_single(picking, configuration, extension='txt')

    def _get_filename_grouped(self, configuration, extension='csv'):
        return super(LaPosteFileGenerator, self)._get_filename_grouped(configuration, extension='txt')

    def _get_rows(self, picking, configuration):
        """
        Returns the rows to create in the file for a picking

        :param browse_record picking: the picking for which we generate a row in the file
        :param browse_record configuration: configuration of the file to generate
        :return: list of rows
        """
        line = LaPosteLine()
        line.reference = picking.name
        address = picking.address_id
        if address:
            line.lastname = address.name or (address.partner_id and address.partner_id.name)
            # if a company, put company name
            if picking.address_id.partner_id.title:
                line.company_name = address.partner_id.name
            line.street1 = address.street or ''
            line.street2 = address.street2 or ''
            line.zip = address.zip or ''
            line.city = address.city or ''
            line.country = address.country_id.code or ''
            line.phone = address.phone or picking.address_id.mobile or ''
        line.weight = "%.2f" % (picking.weight,)
        return [line.get_fields()]

    def _write_rows(self, file_handle, rows, configuration):
        """
        Write the rows in the file (file_handle)

        :param StringIO file_handle: file to write in
        :param rows: rows to write in the file
        :param browse_record configuration: configuration of the file to generate
        :return: the file_handle as StringIO with the rows written in it
        """
        writer = UnicodeWriter(file_handle, delimiter=';', quotechar='"',
                               lineterminator='\n', quoting=csv.QUOTE_ALL)
        writer.writerows(rows)
        return file_handle
