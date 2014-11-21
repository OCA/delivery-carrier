# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2012 Akretion David BEAL <david.beal@akretion.com>
#   Copyright (C) 2012 Akretion Seb BEAU <sebastien.beau@akretion.com>
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
from openerp.tools.translate import _


class DeliveryDepositWizard(orm.TransientModel):
    _name = "delivery.deposit.wizard"
    _description = "Wizard to create deposit slip"
    _rec_name = 'carrier_type'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        return self.pool['delivery.carrier']._get_carrier_type_selection(
            cr, uid, context=context)

    _columns = {
        'carrier_type': fields.selection(
            _get_carrier_type_selection,
            'Type',
            required=True,
            help="Carrier type (combines several delivery methods)"),
    }

    def _prepare_deposit_slip(self, cr, uid, wizard, context=None):
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        return {
            'carrier_type': wizard.carrier_type,
            'company_id': user.company_id.id
        }

    def create_deposit_slip(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context=context)
        picking_obj = self.pool['stock.picking']
        deposit_obj = self.pool['deposit.slip']
        picking_ids = picking_obj.search(
            cr, uid, [
                ('carrier_type', '=', wizard.carrier_type),
                ('deposit_slip_id', '=', False),
                ('state', '=', 'done'),
            ], context=context)
        if picking_ids:
            vals = self._prepare_deposit_slip(cr, uid, wizard, context=context)
            deposit_id = deposit_obj.create(cr, uid, vals, context=context)
            picking_obj.write(
                cr, uid, picking_ids, {
                    'deposit_slip_id': deposit_id,
                }, context=context)
            action = {
                'name': 'Deposit Slip',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_id': deposit_id,
                'view_id': False,
                'res_model': 'deposit.slip',
                'type': 'ir.actions.act_window',
                'nodestroy': False,
                'target': 'current',
            }
            return action
        else:
            raise orm.except_orm(
                _("Picking"),
                _("There is no picking for '%s' carrier \n"
                  "to gather in a deposit slip")
                % wizard.carrier_type)
