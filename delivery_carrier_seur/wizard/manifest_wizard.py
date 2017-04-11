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
from openerp import fields, models, api, exceptions, _
from seur.picking import Picking
from urllib2 import HTTPError


class ManifestWizard(models.TransientModel):
    _inherit = 'manifest.wizard'

    @api.multi
    def get_manifest_file(self):
        self.ensure_one()
        if self.carrier_type == 'seur':
            config = self.carrier_id.seur_config_id

            seur_picking = Picking(
                config.username,
                config.password,
                config.vat,
                config.franchise_code,
                'Odoo',  # seurid
                config.integration_code,
                config.accounting_code
            )
            try:
                connect = seur_picking.test_connection()
                if connect != 'Connection successfully':
                    raise exceptions.Warning(
                        _('Error connecting with SEUR:\n%s' % connect))
            except HTTPError, e:
                raise exceptions.Warning(
                    _('Error connecting with SEUR try later:\n%s' % e))

            data = {
                'date': fields.Datetime.from_string(self.from_date)
            }

            manifiesto = False
            try:
                manifiesto = seur_picking.manifiesto(data)
            except HTTPError, e:
                raise exceptions.Warning(
                    _('Error generating SEUR manifest:\n%s' % e))

            self.write({
                'state': 'file',
                'file_out': manifiesto,
                'filename': ('manifiesto_%s.pdf') % (self.from_date)
            })

            return {
                'name': 'Seur Manifest',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'manifest.wizard',
                'view_id': False,
                'target': 'new',
                'type': 'ir.actions.act_window',
                'domain': [('id', '=', self.id)],
                'context': self.env.context,
                'nodestroy': True,
                'res_id': self.id,
            }
        else:
            return super(ManifestWizard, self).get_manifest_file()
