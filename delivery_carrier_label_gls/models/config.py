# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class GlsConfigSettings(models.TransientModel):
    _name = "gls.config.settings"
    _inherit = "res.config.settings"
    _description = "GLS carrier configuration"

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=_default_company,
    )
    gls_contact_id = fields.Char(related="company_id.gls_contact_id")
    gls_test = fields.Boolean(related="company_id.gls_test")

    @api.onchange("company_id")
    def onchange_company_id(self):
        company = self.company_id
        if company:
            self.gls_contact_id = company.gls_contact_id
            self.gls_test = company.gls_test
