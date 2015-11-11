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

from openerp import models, fields, api


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def generate_carrier_files(self, auto=True,
                               recreate=False):
        """
        Generates all the files for a list of pickings according to
        their configuration carrier file.
        Does nothing on pickings without carrier or without
        carrier file configuration.
        Generate files only for outgoing pickings.

        :param list ids: list of ids of pickings for which we need a file
        :param auto: specify if we call the method from an automatic action
                     (on process on picking as instance)
                     or called manually from the wizard. When auto is True,
                     only the carrier files set as "auto_export"
                     are exported
        :return: True if successful
        """
        carrier_file_ids = {}
        for picking in self:
            if picking.picking_type_id.code != 'outgoing':
                continue
            if not recreate and picking.carrier_file_generated:
                continue
            carrier = picking.carrier_id
            if not carrier:
                continue
            if not carrier.carrier_file_id:
                continue
            if auto and not carrier.carrier_file_id.auto_export:
                continue
            p_carrier_file_id = picking.carrier_id.carrier_file_id.id
            carrier_file_ids.setdefault(p_carrier_file_id, []).append(
                picking.id)

        carrier_files = self.env["delivery.carrier.file"].browse(
            carrier_file_ids.keys())
        for carrier_file in carrier_files:
            carrier_file.generate_files(carrier_file_ids[carrier_file.id])
        return True

    @api.multi
    def action_done(self):
        result = super(stock_picking, self).action_done()
        self.generate_carrier_files(auto=True)
        return result

    carrier_file_generated = fields.Boolean(
        'Carrier File Generated', readonly=True, copy=False,
        help="The file for the delivery carrier has been generated.")


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def write(self, values):
        write_result = super(stock_move, self).write(values)
        if values.get('state') and values['state'] == 'done':
            picking_ids = map(lambda p: p.id, self.mapped('picking_id'))
            done_pickings = self.env['stock.picking'].search([
                ('id', 'in', picking_ids),
                ('state', '=', 'done')
            ])
            if done_pickings:
                done_pickings.generate_carrier_files()
        return write_result
