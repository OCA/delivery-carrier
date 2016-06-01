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

import csv

from openerp.addons.base_delivery_carrier_files.generator import (
    CarrierFileGenerator
)
from openerp.addons.base_delivery_carrier_files.generator import BaseLine
from openerp.addons.base_delivery_carrier_files.csv_writer import UnicodeWriter


class TNTLine(BaseLine):
    fields = (('reference', 15),
              ('name', 30),
              ('street1', 30),
              ('street2', 30),
              ('street3', 30),
              ('city', 30),
              ('zip', 9),
              ('state', 30),
              ('country', 2),
              ('country_name', 30),
              ('phone', 16),
              ('fax', 16),
              ('contact', 22),
              ('tnt_account', 9),
              ('vat', 20),
              ('mail', 50),
              ('address_type', 1),
              ('notes', 50),)


class TNTFileGenerator(CarrierFileGenerator):

    @classmethod
    def carrier_for(cls, carrier_name):
        return carrier_name == 'tnt_express_shipper'

    def _get_rows(self, picking, configuration):
        """
        Returns the rows to create in the file for a picking

        :param browse_record picking: the picking for which we generate a row
               in the file
        :param browse_record configuration: configuration of the file to
               generate
        :return: list of rows
        """
        line = TNTLine()
        line.reference = picking.name
        if picking.address_id:
            line.name = (picking.address_id.partner_id and
                         picking.address_id.partner_id.name)
            line.contact = picking.address_id.name
            line.street1 = picking.address_id.street
            line.street2 = picking.address_id.street2
            line.zip = picking.address_id.zip
            line.state = (picking.address_id.state_id and
                          picking.address_id.state_id.name)
            line.city = picking.address_id.city
            line.country = picking.address_id.country_id.code
            line.country_name = picking.address_id.country_id.name
            line.phone = picking.address_id.phone or picking.address_id.mobile
            line.fax = picking.address_id.fax
            line.vat = picking.address_id.partner_id.vat
            line.mail = picking.address_id.email
        line.tnt_account = configuration.tnt_account
        line.address_type = 'R'
        # according to specs, this field need at least on char
        line.notes = picking.carrier_id and picking.carrier_id.name or '*'
        return [line.get_fields()]

    def _write_rows(self, file_handle, rows, configuration):
        """
        Write the rows in the file (file_handle)

        :param StringIO file_handle: file to write in
        :param rows: rows to write in the file
        :param browse_record configuration: configuration of the file to
               generate
        :return: the file_handle as StringIO with the rows written in it
        """
        writer = UnicodeWriter(file_handle, delimiter=';', quotechar='"',
                               lineterminator='\n', quoting=csv.QUOTE_ALL)
        writer.writerows(rows)
        return file_handle
