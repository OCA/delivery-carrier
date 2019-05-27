from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    cex_test = fields.Boolean(
        string='Correos Express Test Environment')
    cex_username = fields.Char(
        string='Correos Express Username')
    cex_password = fields.Char(
        string='Correos Express Password')
    cex_codRte = fields.Char(
        string='Correos Express codRte')
    cex_solicitante = fields.Char(
        string='Correos Express Solicitante')
