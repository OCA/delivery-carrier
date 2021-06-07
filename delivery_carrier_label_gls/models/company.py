# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    gls_contact_id = fields.Char(
        string="International",
        size=10,
        help="Contact id for GLS International transportation (T8914)",
    )
    gls_test = fields.Boolean(string="Url Test", help="Use testing webservice")
