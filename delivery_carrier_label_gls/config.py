# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm, fields
from . company import ResCompany


CHARGEUR = 'gls_chargeur'


class GlsConfigSettings(orm.TransientModel):
    _name = 'gls.config.settings'

    _description = 'GLS carrier configuration'
    _inherit = ['res.config.settings', 'abstract.config.settings']
    _prefix = 'gls_'
    _companyObject = ResCompany

    _columns = {
        'gls_customer_code': fields.char(
            string='Customer Code',
            readonly=True,
            help="Code for GLS carrier company (T8915)\n"
                 "Information common to whole companies "
                 "to configure in System Parameter"),
        'gls_warehouse': fields.char(
            string='Warehouse',
            readonly=True,
            help="GLS warehouse near customer location (T8700)\n"
                 "Information common to whole companies "
                 "to configure in System Parameter"),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = {}
        param_m = self.pool['ir.config_parameter']
        for field in ['gls_customer_code', 'gls_warehouse']:
            if field in fields:
                ids = param_m.search(
                    cr, uid, [('key', '=', 'carrier_%s' % field)],
                    context=context)
                if not ids:
                    raise orm.except_orm(
                        "Missing parameter",
                        "'%s' key is missing in 'System Parameter':\n"
                        "Add it and set the corresponding value" % field)
                param = param_m.browse(cr, uid, ids, context=context)[0]
                res[field] = param.value
        return res
