# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base_delivery_carrier_files.generator import (
    CarrierFileGenerator
)
from odoo.addons.base_delivery_carrier_files.generator.generic_generator import GenericLine


class GroupedCarrierFileGenerator(CarrierFileGenerator):

    @classmethod
    def carrier_for(cls, carrier_name):
        for subcls in GroupedCarrierFileGenerator.__subclasses__():
            if subcls.carrier_for(carrier_name):
                return subcls
        return False

    def _get_filename_grouped(
            self, configuration, extension='csv', partner_id=False):
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
        if not partner_id:
            res = super(GroupedCarrierFileGenerator, self)._get_filename_grouped(
                configuration, extension=extension)
        else:
            res = "%s_%s_%s.%s" % (
                'out', self._filename_date(), partner_id, extension)
        return res

    def _generate_files_grouped(self, pickings, configuration):
        grouped_pickings = []
        pickings_by_partner = {}
        for picking in pickings:
            if picking.partner_id.one_delivery_by_picking:
                grouped_pickings.append(picking)
            else:
                if picking.partner_id.id not in pickings_by_partner:
                    pickings_by_partner[picking.partner_id.id] = picking
                else:
                    pickings_by_partner[picking.partner_id.id] |= picking
        files = super(GroupedCarrierFileGenerator, self)._generate_files_grouped(
            grouped_pickings, configuration)
        # files:: (filename, file_content, [p.id for p in pickings])
        first_file = files.pop(0)
        filename = first_file[0]
        file_content = first_file[1]
        result_picking_list = first_file[2]

        grouped_rows, grouped_picking_ids = self._get_grouped_rows(
            pickings_by_partner, configuration)
        grouped_content = self._get_file(grouped_rows, configuration)
        file_content += grouped_content
        result_picking_list += grouped_picking_ids
        files.append((filename, file_content, result_picking_list))
        return files

    def _get_grouped_rows(self, pickings_by_partner, configuration):
        grouped_picking_ids = []

        test_line = GenericLine()
        fields = test_line.fields
        name_index = fields.index('name')
        weight_index = fields.index('weight')
        grouped_rows = []
        for key, cur_pickings in pickings_by_partner.items():
            cur_row = False
            for picking in cur_pickings:
                rows = self._get_rows(picking, configuration)
                row = rows[0]
                if not cur_row:
                    cur_row = row
                else:
                    cur_row[name_index] += ',' + row[name_index]
                    cur_weight = float(cur_row[weight_index].replace(',', '.'))
                    cur_row[weight_index] = cur_weight
            grouped_rows.append(cur_row)
            grouped_picking_ids += cur_pickings.ids
        return (grouped_rows, grouped_picking_ids)


def new_file_generator(carrier_name):
    for cls in CarrierFileGenerator.__subclasses__():
        carrier_for = cls.carrier_for(carrier_name)
        if carrier_for:
            if isinstance(carrier_for, type):
                return carrier_for(carrier_name)
            else:
                return cls(carrier_name)
    raise ValueError
