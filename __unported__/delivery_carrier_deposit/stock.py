# -*- encoding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2012 Akretion David BEAL <david.beal@akretion.com>
#   Copyright (C) 2012 Akretion Sebastien BEAU <sebastien.beau@akretion.com>
#   Copyright (C) 2012 Akretion Benoit GUILLOT <benoit.guillot@akretion.com>
#   Copyright (C) 2013 Akretion Chafique DELLI <chafique.delli@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm


class DepositSlip(orm.Model):
    _name = 'deposit.slip'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        return self.pool['delivery.carrier']._get_carrier_type_selection(
            cr, uid, context=context)

    _columns = {
        'name': fields.char(
            'Name',
            readonly=True,
            states={'draft': [('readonly', False)]},),
        'carrier_type': fields.selection(
            _get_carrier_type_selection,
            'Type',
            readonly=True,
            help="Carrier type (combines several delivery methods)"),
        'picking_ids': fields.one2many(
            'stock.picking',
            'deposit_slip_id',
            'Pickings',
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'create_date': fields.datetime(
            'Created',
            readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
        ], 'Status', readonly=True),
        'company_id': fields.many2one(
            'res.company',
            'Company'),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context:
            obj.pool['ir.sequence'].next_by_code(
                cr, uid, 'delivery.deposit', context=context),
        'state': 'draft'
    }

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "'Deposit slip' name must be unique!"),
    ]

    _order = 'id desc'

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'name': self.pool['ir.sequence'].next_by_code(
                cr, uid, 'delivery.deposit', context=context),
            'deposit_slip_id': False,
        })
        return super(DepositSlip, self).copy(
            cr, uid, id, default, context=context)

    def create_edi_file(self, cr, uid, ids, context=None):
        """
        Override this method for the proper carrier
        """
        return True

    def validate_deposit(self, cr, uid, ids, context=None):
        self.create_edi_file(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'done'})
        return True


class StockPicking(orm.Model):
    _inherit = "stock.picking"

    _columns = {
        'deposit_slip_id': fields.many2one('deposit.slip', 'Deposit slip'),
    }


class StockPickingOut(orm.Model):
    _inherit = "stock.picking.out"

    _columns = {
        'deposit_slip_id': fields.many2one('deposit.slip', 'Deposit slip'),
    }


class DeliveryCarrier(orm.Model):
    _inherit = "delivery.carrier"

    _columns = {
        'deposit_slip': fields.boolean(
            'Deposit Slip',
            help="Allow to create a 'Deposit slip' "
                 "report on picking out (deliveries)"),
    }
