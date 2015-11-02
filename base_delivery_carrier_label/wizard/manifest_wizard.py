##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#                  Ismael Calvo <ismael.calvo@factorlibre.com>
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
from openerp import models, fields, api, exceptions, _


class ManifestWizard(models.Model):
    _name = 'manifest.wizard'
    _description = 'Delivery carrier manifest wizard'

    @api.model
    def _get_carrier_type_selection(self):
        carrier_obj = self.env['delivery.carrier']
        return carrier_obj._get_carrier_type_selection()

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
        states={'done': [('readonly', True)]},
        required=True
    )
    carrier_type = fields.Selection(
        related='carrier_id.type',
        string='Carrier Type',
        readonly=True,
    )
    from_date = fields.Datetime('From Date', required=True)
    to_date = fields.Datetime('To Date')
    file_out = fields.Binary('Manifest', readonly=True)
    filename = fields.Char('File Name', readonly=True)
    notes = fields.Text('Result', readonly=True)
    state = fields.Selection([
        ('init', 'Init'),
        ('file', 'File'),
        ('end', 'END')
    ], string='State', readonly=True, default='init')

    @api.one
    def get_manifest_file(self):
        raise exceptions.Warning(_("Manifest not implemented for '%s' "
                                   "carrier type.") % self.carrier_type)
