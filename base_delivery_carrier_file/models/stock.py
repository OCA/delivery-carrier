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

from openerp import models, api, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    carrier_file_generated = fields.Boolean(
        string='Carrier File Generated',
        readonly=True,
        copy=False,
        help="The file for the delivery carrier has been generated.")

    @api.multi
    def generate_carrier_files(self, auto=True, recreate=False):
        """
        Generates all the files for a list of pickings according to
        their configuration carrier file.
        Does nothing on pickings without carrier or without
        carrier file configuration.
        Generate files only for outgoing pickings.
        :param auto: specify if we call the method from an automatic action
                     (on process on picking as instance)
                     or called manually from the wizard. When auto is True,
                     only the carrier files set as "auto_export"
                     are exported
        :return: True if successful
        """
        carrier_files = {}
        pickings = self.filtered(
            lambda p:
                (not p.carrier_file_generated or p.recreate)
                and p.carrier_id and p.carrier_id.carrier_file_id
                and (p.carrier_id.carrier_file_id.auto_export or not auto)
        )

        carrier_files = pickings.mapped('carrier_id.carrier_file_id')

        for carrier_file in carrier_files:
            pickings_by_carrier_file = pickings.filtered(
                lambda p: p.carrier_id.carrier_file_id == carrier_file)
            carrier_file.generate_files(pickings_by_carrier_file)
        return True

    @api.multi
    def do_new_transfer(self):
        result = super(StockPicking, self).do_new_transfer()
        self.generate_carrier_files(auto=True)
        return result
