# coding: utf-8
# © 2015 David BEAL @ Akretion
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
    gls_traceability = fields.Boolean(
        string='Traceability',
        help="Record traceability informations in Delivery Order "
             "attachment: web service request and response")
    gls_generate_label = fields.Boolean(
        string='Automatically Generate Label',
        help="Generate label when delivery is done")
    gls_test = fields.Boolean(
        string='Url Test',
        help="Use testing webservice")
