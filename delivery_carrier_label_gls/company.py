# -*- coding: utf-8 -*-
##############################################################################
#
#  license AGPL version 3 or later
#  see license in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm, fields


class ResCompany(orm.Model):

    _inherit = "res.company"

    _columns = {
        'gls_fr_contact_id': fields.char(
            'France',
            size=10,
            help='Contact id for GLS France tranportation (T8914)'),
        'gls_inter_contact_id': fields.char(
            'International',
            size=10,
            help='Contact id for GLS International transportation (T8914)'),
        'gls_test': fields.boolean(
            'Url Test',
            help="Check if requested webservice is test plateform")
    }
