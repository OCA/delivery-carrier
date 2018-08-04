# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class SeurConfig(models.Model):
    _name = 'seur.config'

    name = fields.Char('Name', required=True)
    vat = fields.Char('VAT', required=True)
    integration_code = fields.Char('Integration Code', required=True)
    accounting_code = fields.Char('Accounting Code', required=True)
    franchise_code = fields.Char('Franchise Code', required=True)
    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    file_type = fields.Selection([
        ('pdf', 'PDF'),
        ('txt', 'TXT')
    ], string="File type", required=True)
