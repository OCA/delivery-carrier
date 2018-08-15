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

import os
import logging

from .generator import new_file_generator
from openerp import models, api, fields, _
from openerp.exceptions import UserError


class CarrierFile(models.Model):
    _name = 'delivery.carrier.file'

    @api.model
    def get_type_selection(self):
        """
        Has to be inherited to add carriers
        """
        return [('generic', 'Generic')]

    @api.model
    def get_write_mode_selection(self):
        """
        Selection can be inherited to add more write modes
        """
        return [('disk', 'Disk')]

    name = fields.Char(
        string='Name',
        size=64,
        required=True)
    type = fields.Selection(
        get_type_selection,
        'Type',
        required=True)
    group_pickings = fields.Boolean(
        string='Group all pickings in one file',
        help='All the pickings will be grouped in the same file. '
             'Has no effect when the files are automatically exported at '
             'the delivery order process.')
    write_mode = fields.Selection(
        get_write_mode_selection,
        string='Write on',
        required=True)
    export_path = fields.Char(
        string='Export Path',
        size=256)
    auto_export = fields.Boolean(
        string='Export at delivery order process',
        help='The file will be automatically generated when a delivery order '
             'is processed. If activated, each delivery order will be '
             'exported in a separate file.')

    @api.multi
    def _write_file(self, filename, file_content):
        """
        Method responsible of writing the file, on the filesystem or
        by inheriting the module, in the document module as instance

        :param tuple filename: name of the file to write
        :param tuple file_content: content of the file to write
        :return: True if write is successful
        """
        self.ensure_one()
        if not self.export_path:
            raise UserError(
                _('Error,\nExport path is not defined for carrier file %s') %
                (self.name,))
        full_path = os.path.join(self.export_path, filename)
        with open(full_path, 'w') as file_handle:
            file_handle.write(file_content)
        return True

    @api.multi
    def _generate_files(self, pickings):
        """
        Generate one or more files according to carrier_file configuration
        for all picking_ids

        :param list pickings: pickings for which
                                 we have to generate a file
        :return: True if successful
        """
        self.ensure_one()
        ctx = self.env.context.copy()
        log = logging.getLogger('delivery.carrier.file')
        file_generator = new_file_generator(self.type)
        # must return a list of generated pickings ids to update
        files = file_generator.generate_files(pickings, self)
        if self.auto_export:
            ctx['picking_id'] = pickings and pickings[0].id
        for f in files:
            filename, file_content, picking_ids = f
            # we pass the errors because the files can still be
            # generated manually
            # at first I would like to open a new cursor and
            # commit the write after each file created
            # but I encountered lock because the picking
            # was already modified in the current transaction
            try:
                if self.with_context(ctx)._write_file(filename, file_content):
                    pickings.write({'carrier_file_generated': True})
            except Exception as e:
                log.exception("Could not create the picking file "
                              "for pickings %s: %s",
                              pickings.ids, e)
        return True

    @api.multi
    def generate_files(self, pickings):
        """
        Generate one or more files according to carrier_file
        configuration for all picking_ids
        One type of carrier file is generated at a time which can
        generate one or many files.

        :param list pickings: pickings for
                                 which we have to generate a file
        :return: True if successful
        """
        self.ensure_one()
        return self._generate_files(pickings)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    carrier_file_id = fields.Many2one(
        comodel_name='delivery.carrier.file',
        string='Carrier File')
