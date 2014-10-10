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


class ResCompany(orm.Model):

    _inherit = "res.company"

    _columns = {
        'gls_chargeur': fields.char(
            'Chargeur',
            size=5,
            help='Chargeur code for GLS carrier company'),
        'gls_customer_code': fields.char(
            'Customer Code',
            size=10,
            help='Code for GLS carrier company (T8915)'),
        'gls_business_contact_id': fields.char(
            'Business Product',
            size=10,
            help='Contact id for GLS carrier (T8914)'),
        'gls_euro_contact_id': fields.char(
            'Euro Product',
            size=10,
            help='Contact id for Euro GLS carrier (T8914)'),
        'gls_global_contact_id': fields.char(
            'Global Product',
            size=10,
            help='Contact id for Global GLS carrier (T8914)'),
        'gls_warehouse_code': fields.char(
            'Warehouse Code',
            size=6,
            help='GLS warehouse near customer location (T8700)'),
        'gls_test': fields.boolean(
            'Url Test',
            help="Check if requested webservice is test plateform")
    }
