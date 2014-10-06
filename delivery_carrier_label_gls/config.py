# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm
from . company import ResCompany


class GlsConfigSettings(orm.TransientModel):
    _name = 'gls.config.settings'

    _description = 'GLS carrier configuration'
    _inherit = ['res.config.settings', 'abstract.config.settings']
    _prefix = 'gls_'
    _companyObject = ResCompany
