# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv

from ..csv_writer import UnicodeWriter
from .base_line import BaseLine
from .file_generator import CarrierFileGenerator


class GenericLine(BaseLine):
    fields = (
        "reference",
        "name",
        "contact",
        "street1",
        "street2",
        "zip",
        "city",
        "state",
        "country_code",
        "phone",
        "mail",
        "delivery_name",
        "weight",
    )


class LaPosteFileGenerator(CarrierFileGenerator):
    @classmethod
    def carrier_for(cls, carrier_name):
        return carrier_name == "generic"

    def _get_rows(self, picking, configuration):
        """
        Returns the rows to create in the file for a picking

        :param browse_record picking: the picking for which
                                      we generate a row in the file
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: list of rows
        """
        line = GenericLine()
        line.reference = picking.name
        partner = picking.partner_id
        if partner:
            line.name = partner.name
            line.contact = partner.name
            line.street1 = partner.street
            line.street2 = partner.street2
            line.zip = partner.zip
            line.city = partner.city
            line.state = (partner.state_id and partner.state_id.name) or False
            line.country_code = (
                partner.country_id and partner.country_id.code
            ) or False
            line.phone = partner.phone or partner.mobile
            line.mail = partner.email
        line.delivery_name = (picking.carrier_id and picking.carrier_id.name) or False
        line.weight = "{:.2f}".format(picking.weight)
        return [line.get_fields()]

    def _write_rows(self, file_handle, rows, configuration):
        """
        Write the rows in the file (file_handle)

        :param StringIO file_handle: file to write in
        :param rows: rows to write in the file
        :param browse_record configuration: configuration of
                                            the file to generate
        :return: the file_handle as StringIO with the rows written in it
        """
        writer = UnicodeWriter(
            file_handle,
            delimiter=",",
            quotechar='"',
            lineterminator="\n",
            quoting=csv.QUOTE_ALL,
        )
        writer.writerows(rows)
        return file_handle
