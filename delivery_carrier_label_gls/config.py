# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 2014 Akretion
#    @author David BEAL <david.beal@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import orm, fields
from . company import ResCompany


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
