# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2017 PESOL - Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class ManifestWizard(models.TransientModel):
    _inherit = 'manifest.wizard'

    @api.multi
    def get_manifest_file(self):
        self.ensure_one()
        if self.carrier_type == 'seur':
            config = self.carrier_id.seur_config_id
            data = {
                'date': fields.Date.from_string(self.from_date)
            }
            manifiesto = config.manifiesto(data)
            if not manifiesto:
                raise UserError(
                    _("Manifest no generated"))

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
