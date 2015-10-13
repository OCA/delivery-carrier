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


class BaseLine(object):

    """
    This class can be used to generate a row of data
    easily and get the full row in a list
    The "fields" class variable is used to define
    the columns of the row (keep the order).

    Fields can be a tuple of fields ('field1', 'field2', 'field3', ...)
    or a tuple which contains tuple of fields with (name, max length).
    If a width is defined, the fields content will be cut at max length
    when we get the row

    Empty fields '' can be used to leave columns empty.

    This class has purpose to be subclassed e.g.

    class MyLine(BaseLine):
        fields = ('field1', 'field2', '', 'field4', 'field5')

    row = MyLine()
    row.field1 = 'x'
    row.field2 = 'y'
    row.field4 = 'z'
    row.get_fields()
    => ['x', 'y', '', 'z', '']

    Or

    class MyLine(BaseLine):
        fields = (('field1', 10),
                  ('field2', 4))

    row = MyLine()
    row.field1 = 'x'
    row.field2 = 'long_name'
    row.get_fields()
    => ['x', 'long']

    You can also mix unlimited width fields and limited
    class MyLine(BaseLine):
        fields = ('field1',
                  ('field2', 4))

    row = MyLine()
    row.field1 = 'x'
    row.field2 = 'long_name'
    row.get_fields()
    => ['x', 'long']
    """
    fields = ()

    def __init__(self):
        """
        Create an instance attribute for each field
        in the fields class property
        Unless if the field name is empty
        (in order to leave a column empty in the row)
        """
        if not self.fields:
            raise ValueError("Fields Missing")
        for field in self.fields:
            field_name, _ = self._field_definition(field)
            if not field_name:
                continue
            setattr(self, field_name, '')

    @staticmethod
    def _field_definition(field):
        """
        Return the field name and its max length (optional)
        as declared in the class for one slot of the class attribute "fields"

        :param field: a field has it is defined in
                      the class attribute "fields"
        :return: field name and its optional max length
        """
        width = False
        if field in (False, None):
            field_name = ''
        elif isinstance(field, tuple):
            field_name, width = field
        elif isinstance(field, str):
            field_name = field
        else:
            raise ValueError("Wrong field definition for field %s" % (field,))
        return field_name, width

    def get_fields(self):
        """
        According to the class attribute "fields",
        generate a row with all the value of the line.
        If a width is defined on some fields,
        their content is cut to their maximal length.

        :return: a list of values for each field in the
                 order of the class attribute "fields"
        """
        res = []
        for field in self.fields:
            field_name, width = self._field_definition(field)
            if field_name:
                value = getattr(self, field_name)
                if value in (False, None):
                    value = ''
                elif not isinstance(value, (str, unicode)):
                    value = unicode(value)
                if width:
                    value = value[0:width]
            else:
                value = ''
            res.append(value)
        return res

    def get_header(self):
        """
        Returns a list of field's names respecting
        the order of the class attribute "fields"

        :return: a list of field names
        """
        res = []
        for field in self.fields:
            field_name, _ = self._field_definition(field)
            res.append(field_name)
        return res
