# -*- coding: utf-8 -*-
# © 2013-2015 David BEAL <david.beal@akretion.com>
# © 2017 Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import UserError

from . company import ResCompany


class AsmConfigSettings(models.TransientModel):
    _name = 'asm.config.settings'

    _description = 'ASM carrier configuration'
    _inherit = ['res.config.settings', 'abstract.config.settings']
    _prefix = 'asm_'
    _companyObject = ResCompany

    asm_customer_code = fields.Char(
        string='Customer Code',
        readonly=True,
        help="Code for ASM carrier company (T8915)\n"
        "Information common to whole companies "
        "to configure in System Parameter")
    asm_warehouse = fields.Char(
        string='Warehouse',
        readonly=True,
        help="ASM warehouse near customer location (T8700)\n"
        "Information common to whole companies "
        "to configure in System Parameter")

    @api.model
    def default_get(self, fields):
        res = {}
        param_m = self.env['ir.config_parameter']
        for field in ['asm_customer_code', 'asm_warehouse']:
            if field in fields:
                param = param_m.search(
                    [('key', '=', 'carrier_%s' % field)])
                if not param:
                    raise UserError(
                        _("Missing parameter",
                          "'%s' key is missing in 'System Parameter':\n"
                          "Add it and set the corresponding value") % field)
                res[field] = param.value
        return super(AsmConfigSettings, self).default_get(fields)
