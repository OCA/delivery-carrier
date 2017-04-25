# -*- coding: utf-8 -*-
# Copyright 2017 PESOL - Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import csv

from openerp.addons.base_delivery_carrier_file.models.generator import (
    CarrierFileGenerator,
    BaseLine
)
from openerp.addons.base_delivery_carrier_file.models.csv_writer import (
    UnicodeWriter
)


class GlsLine(BaseLine):
    fields = (
        'reference',
        'name',
        '',
        '',
        'street',
        'country_code',
        'zip',
        'city',
        'weight',
        'refound_code',
        'refound_amount',
        'number_of_packages',
        'phone',
        'mail',
        '',
        'details')


class GlsFileGenerator(CarrierFileGenerator):

    @classmethod
    def carrier_for(cls, carrier_name):
        return carrier_name == 'gls'

    def _get_filename_single(self, picking, configuration, extension='csv'):
        return super(GlsFileGenerator, self
                     )._get_filename_single(picking, configuration,
                                            extension='csv')

    def _get_filename_grouped(self, configuration, extension='csv'):
        return super(GlsFileGenerator, self
                     )._get_filename_grouped(configuration, extension='txt')

    def _get_rows(self, picking, configuration):
        """
        Returns the rows to create in the file for a picking

        :param browse_record picking: the picking for which we generate a row
               in the file
        :param browse_record configuration: configuration of the file to
               generate
        :return: list of rows
        """
        line = GlsLine()
        line.reference = picking.name
        address = picking.partner_id
        if address:
            line.name = address.name or (address.partner_id
                                         and address.partner_id.name)
            line.street = '%s, %s' % (address.street, address.street2)
            line.country = address.country_id.code
            line.zip = address.zip
            line.city = address.city
            line.phone = address.phone or address.mobile
            line.mail = address.email
        line.weight = "%.2f" % (picking.weight,)
        line.number_of_packages = picking.number_of_packages
        # TODO refound
        line.refound_code = ''
        line.refount_amount = '0,00'
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
        writer = UnicodeWriter(file_handle, delimiter=';',
                               lineterminator='\n', quoting=csv.QUOTE_ALL)
        writer.writerows(rows)
        return file_handle
