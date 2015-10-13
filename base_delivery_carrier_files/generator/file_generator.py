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

import string
import datetime
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


class CarrierFileGenerator(object):

    def __init__(self, carrier_name):
        self.carrier_name = carrier_name

    @classmethod
    def carrier_for(cls, carrier_name):
        return False

    @staticmethod
    def sanitize_filename(name):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return ''.join(c for c in name if c in valid_chars)

    @staticmethod
    def _filename_date(timestamp=None):
        """
        Return a date to put in the filename, formatted like :
        20120214_094435 for 2012 february 14. at 09 hours 44 and 35 seconds

        :param datetime timestamp: optional datetime value to use instead of
                                   the current date and time
        :return: a date as str
        """
        date = timestamp or datetime.datetime.now()
        return date.strftime('%Y%m%d_%H%M%S')

    def generate_files(self, pickings, configuration):
        """
        Base method to generate the pickings files, one file per picking
        It returns a list of tuple with a filename, its content and a
        list of pickings ids contained in the file

        :param browse_record pickings: list of browsable pickings records
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: list of tuple with files to create like:
                 [('filename1', file, [picking ids]),
                  ('filename2', file2, [picking ids])]
        """
        if configuration.group_pickings:
            return self._generate_files_grouped(pickings, configuration)
        else:
            return self._generate_files_single(pickings, configuration)

    def _get_filename_single(self, picking, configuration, extension='csv'):
        """
        Generate the filename for a picking when one file is
        generated for one picking
        Inherit and implement in subclasses.

        :param browse_record picking: picking for which we generate a file
        :param browse_record configuration: configuration of
                                            the file to generate
        :param str extension: extension of the file to create, csv by default
        :return: a string with the name of the file
        """
        return "%s_%s.%s" % (picking.name, self._filename_date(), extension)

    def _get_filename_grouped(self, configuration, extension='csv'):
        """
        Generate the filename for a file which group many pickings.
        When pickings are grouped in one file, the filename cannot
        be based on the picking data
        Inherit and implement in subclasses.

        :param browse_record configuration: configuration of
                                            the file to generate
        :param str extension: extension of the file to create, csv by default
        :return: a string with the name of the file
        """
        return "%s_%s.%s" % ('out', self._filename_date(), extension)

    def _get_rows(self, picking, configuration):
        """
        Returns the rows to create in the file for a picking.
        Inherit and implement in subclasses.

        :param browse_record picking: the picking for which
                                      we generate a row in the file
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: list of rows
        """
        return NotImplementedError

    def _write_rows(self, file_handle, rows, configuration):
        """
        Write the rows in the file (file_handle).
        Inherit and implement in subclasses.

        :param StringIO file_handle: file to write in
        :param rows: rows to write in the file
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: the file_handle as StringIO with the rows written in it
        """
        return NotImplementedError

    def _get_file(self, rows, configuration):
        """
        Create a file in a StringIO, call the method which generates
        the content of the file
        and returns the content of the file

        :param list rows: rows to write in the file, the way they are
                          written to the file is defined in _write_rows
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: content of the file
        """
        file_handle = StringIO.StringIO()
        try:
            file_handle = self._write_rows(file_handle,
                                           rows, configuration)
            file_content = file_handle.getvalue()
        finally:
            file_handle.close()
        return file_content

    def _generate_files_single(self, pickings, configuration):
        """
        Base method to generate the pickings files, one file per picking
        It returns a list of tuple with a filename, its content and a
        list of pickings ids in the file

        :param browse_record pickings: list of browsable pickings records
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: list of tuple with files to create like:
                 [('filename1', file, [picking ids]),
                  ('filename2', file2, [picking ids])]
        """
        files = []
        for picking in pickings:
            filename = self._get_filename_single(picking, configuration)
            filename = self.sanitize_filename(filename)
            rows = self._get_rows(picking, configuration)
            file_content = self._get_file(rows, configuration)
            files.append((filename, file_content, [picking.id]))
        return files

    def _generate_files_grouped(self, pickings, configuration):
        """
        Base method to generate the pickings files, one file
        for all pickings
        It returns a list of tuple with a filename, its content
         and a list of pickings ids in the file

        :param browse_record pickings: list of browsable pickings records
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: list of tuple with files to create like:
                 [('filename1', file, [picking ids]),
                  ('filename2', file2, [picking ids])]
        """
        files = []
        rows = []
        filename = self._get_filename_grouped(configuration)
        filename = self.sanitize_filename(filename)
        for picking in pickings:
            rows += self._get_rows(picking, configuration)
        file_content = self._get_file(rows, configuration)
        files.append((filename, file_content, [p.id for p in pickings]))
        return files


def new_file_generator(carrier_name):
    for cls in CarrierFileGenerator.__subclasses__():
        if cls.carrier_for(carrier_name):
            return cls(carrier_name)
    raise ValueError
