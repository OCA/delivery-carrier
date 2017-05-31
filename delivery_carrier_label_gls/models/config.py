# -*- coding: utf-8 -*-
# © 2013-2015 David BEAL <david.beal@akretion.com>
# © 2017 Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields, _
from openerp.exceptions import UserError

from . company import ResCompany


class GlsConfigSettings(models.TransientModel):
    _name = 'gls.config.settings'

    _description = 'GLS carrier configuration'
    _inherit = ['res.config.settings', 'abstract.config.settings']
    _prefix = 'gls_'
    _companyObject = ResCompany

    gls_customer_code = fields.Char(
        string='Customer Code',
        readonly=True,
        help="Code for GLS carrier company (T8915)\n"
        "Information common to whole companies "
        "to configure in System Parameter")
    gls_warehouse = fields.Char(
        string='Warehouse',
        readonly=True,
        help="GLS warehouse near customer location (T8700)\n"
        "Information common to whole companies "
        "to configure in System Parameter")

    @api.model
    def default_get(self, fields):
        res = {}
        param_m = self.env['ir.config_parameter']
        for field in ['gls_customer_code', 'gls_warehouse']:
            if field in fields:
                param = param_m.search(
                    [('key', '=', 'carrier_%s' % field)])
                if not param:
                    raise UserError(
                        _("Missing parameter",
                          "'%s' key is missing in 'System Parameter':\n"
                          "Add it and set the corresponding value") % field)
                res[field] = param.value
        return super(GlsConfigSettings, self).default_get(fields)
