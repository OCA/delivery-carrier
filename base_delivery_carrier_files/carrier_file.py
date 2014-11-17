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

from openerp.osv import orm, fields
from .generator import new_file_generator
from tools.translate import _


class CarrierFile(orm.Model):
    _name = 'delivery.carrier.file'

    def get_type_selection(self, cr, uid, context=None):
        """
        Has to be inherited to add carriers
        """
        return [('generic', 'Generic')]

    def get_write_mode_selection(self, cr, uid, context=None):
        """
        Selection can be inherited to add more write modes
        """
        return [('disk', 'Disk')]

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'type': fields.selection(get_type_selection, 'Type', required=True),
        'group_pickings': fields.boolean('Group all pickings in one file',
                                         help='All the pickings will be '
                                              'grouped in the same file. '
                                              'Has no effect when the files '
                                              'are automatically exported at '
                                              'the delivery order process.'),
        'write_mode': fields.selection(get_write_mode_selection,
                                       'Write on',
                                       required=True),
        'export_path': fields.char('Export Path', size=256),
        'auto_export': fields.boolean('Export at delivery order process',
                                      help='The file will be automatically '
                                           'generated when a delivery order '
                                           'is processed. If activated, each '
                                           'delivery order will be exported '
                                           'in a separate file.'),
    }

    def _write_file(self, cr, uid, carrier_file, filename, file_content,
                    context=None):
        """
        Method responsible of writing the file, on the filesystem or
        by inheriting the module, in the document module as instance

        :param browse_record carrier_file: browsable carrier.file
                                           (configuration)
        :param tuple filename: name of the file to write
        :param tuple file_content: content of the file to write
        :return: True if write is successful
        """
        if not carrier_file.export_path:
            raise orm.except_orm(_('Error'),
                                 _('Export path is not defined '
                                   'for carrier file %s') %
                                 (carrier_file.name,))
        full_path = os.path.join(carrier_file.export_path, filename)
        with open(full_path, 'w') as file_handle:
            file_handle.write(file_content)
        return True

    def _generate_files(self, cr, uid, carrier_file, picking_ids,
                        context=None):
        """
        Generate one or more files according to carrier_file configuration
        for all picking_ids

        :param browse_record carrier_file: browsable carrier file
                                           configuration
        :param list picking_ids: list of ids of pickings for which
                                 we have to generate a file
        :return: True if successful
        """
        if context is None:
            context = {}
        picking_obj = self.pool.get('stock.picking')
        log = logging.getLogger('delivery.carrier.file')
        file_generator = new_file_generator(carrier_file.type)
        pickings = [picking for picking in
                    picking_obj.browse(cr, uid, picking_ids, context=context)]
        # must return a list of generated pickings ids to update
        files = file_generator.generate_files(pickings, carrier_file)
        if carrier_file.auto_export:
            context['picking_id'] = pickings and pickings[0].id
        for f in files:
            filename, file_content, picking_ids = f
            # we pass the errors because the files can still be
            # generated manually
            # at first I would like to open a new cursor and
            # commit the write after each file created
            # but I encountered lock because the picking
            # was already modified in the current transaction
            try:
                if self._write_file(cr, uid, carrier_file, filename,
                                    file_content, context=context):
                    picking_obj.write(cr, uid, picking_ids,
                                      {'carrier_file_generated': True},
                                      context=context)
            except Exception as e:
                log.exception("Could not create the picking file "
                              "for pickings %s: %s",
                              picking_ids, e)
        return True

    def generate_files(self, cr, uid, carrier_file_id, picking_ids,
                       context=None):
        """
        Generate one or more files according to carrier_file
        configuration for all picking_ids
        One type of carrier file is generated at a time which can
        generate one or many files.

        :param int carrier_file_id: id of the carrier file configuration
        :param list picking_ids: list of ids of pickings for
                                 which we have to generate a file
        :return: True if successful
        """
        if not isinstance(carrier_file_id, (int, long)):
            if len(carrier_file_id) > 1:
                raise Exception('Code Error: you have to export '
                                'only one carrier at a time.')
            else:
                carrier_file_id = carrier_file_id[0]
        carrier_file = self.browse(cr, uid, carrier_file_id, context=context)
        return self._generate_files(cr, uid, carrier_file, picking_ids,
                                    context=context)


class delivery_carrier(orm.Model):
    _inherit = 'delivery.carrier'

    _columns = {
        'carrier_file_id': fields.many2one('delivery.carrier.file',
                                           'Carrier File')
    }
