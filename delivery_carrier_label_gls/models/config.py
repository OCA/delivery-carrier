# coding: utf-8
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, _, fields
from openerp.exceptions import Warning as UserError


class GlsConfigSettings(models.TransientModel):
    _name = 'gls.config.settings'
    _inherit = 'res.config.settings'
    _description = 'GLS carrier configuration'

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        required=True, default=_default_company)
    customer_code = fields.Char(
        string='Customer Code',
        readonly=True, oldname='gls_customer_code',
        help="Code for GLS carrier company (T8915)\n"
             "Settings for all companies "
             "to be configured in System Parameter")
    warehouse = fields.Char(
        string='Warehouse',
        readonly=True, oldname='gls_warehouse',
        help="GLS warehouse near customer location (T8700)\n"
             "Settings for all companies "
             "to be configured in System Parameter")
    fr_contact_id = fields.Char(
        related="company_id.gls_fr_contact_id")
    inter_contact_id = fields.Char(
        related="company_id.gls_inter_contact_id")
    traceability = fields.Boolean(
        related="company_id.gls_traceability")
    generate_label = fields.Boolean(
        related="company_id.gls_generate_label")
    test = fields.Boolean(
        related="company_id.gls_test")

    @api.onchange('company_id')
    def onchange_company_id(self):
        # update related fields
        if not self.company_id:
            return
        company = self.company_id
        self.fr_contact_id = company.gls_fr_contact_id
        self.inter_contact_id = company.gls_inter_contact_id
        self.traceability = company.gls_traceability
        self.generate_label = company.gls_generate_label
        self.test = company.gls_test

    @api.model
    def default_get(self, fields):
        res = super(GlsConfigSettings, self).default_get(fields)
        param_m = self.env['ir.config_parameter']
        for field in ['customer_code', 'warehouse']:
            if field in fields:
                configs = param_m.search(
                    [('key', '=', 'carrier_gls_%s' % field)])
                if not configs:
                    raise UserError(
                        _("'%s' key is missing in 'System Parameter':\n"
                          "Add it and set the corresponding value.") % field)
                res[field] = configs[0].value
        return res
