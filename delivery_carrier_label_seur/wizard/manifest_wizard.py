# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2017 PESOL - Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, api, fields, _
from seur.picking import Picking
from openerp.exceptions import Warning


class ManifestWizard(models.TransientModel):
    _inherit = 'manifest.wizard'

    @api.multi
    def get_manifest_file(self):
        self.ensure_one()
        if self.carrier_type == 'seur':
            config = self.carrier_id.seur_config_id
            context = {
                'pdf': True
            }
            data = {
                'date': fields.Date.from_string(self.from_date)
            }
            manifiesto = False
            with Picking(
                config.username,
                config.password,
                config.vat,
                config.franchise_code,
                'Odoo',  # seurid
                config.integration_code,
                config.accounting_code,
                100,
                context
            ) as seur_picking:
                manifiesto = seur_picking.manifiesto(data)
            if not manifiesto:
                raise Warning(
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
