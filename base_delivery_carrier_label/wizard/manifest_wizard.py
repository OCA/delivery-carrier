# -*- coding: utf-8 -*-
# Copyright 2015 FactorLibre (http://www.factorlibre.com)
#        Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, exceptions, _


class ManifestWizard(models.TransientModel):
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
        selection='_get_carrier_type_selection',
        related='carrier_id.carrier_type',
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
    ], readonly=True, default='init')

    @api.one
    def get_manifest_file(self):
        raise exceptions.Warning(_("Manifest not implemented for '%s' "
                                   "carrier type.") % self.carrier_type)
