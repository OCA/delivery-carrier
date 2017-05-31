# -*- coding: utf-8 -*-
# © 2013-2015 David BEAL <david.beal@akretion.com>
# © 2017 Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    gls_fr_contact_id = fields.Char(
        string='France',
        size=10,
        help='Contact id for GLS France tranportation (T8914)')
    gls_inter_contact_id = fields.Char(
        string='International',
        size=10,
        help='Contact id for GLS International transportation (T8914)')
    name = fields.Boolean(
        string='Url Test',
        help="Check if requested webservice is test plateform")
