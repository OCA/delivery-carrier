# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2012-2014 Akretion France (www.akretion.com)
#   @author: David BEAL <david.beal@akretion.com>
#   @author: Sebastien BEAU <sebastien.beau@akretion.com>
#   @author: Chafique DELLI <chafique.delli@akretion.com>
#   @author: Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp import fields, models, api, _
from openerp.exceptions import Warning


class DeliveryDepositWizard(models.TransientModel):
    _name = "delivery.deposit.wizard"
    _description = "Wizard to create Deposit Slip"
    _rec_name = 'carrier_type'

    @api.model
    def _get_carrier_type_selection(self):
        return self.env['delivery.carrier']._get_carrier_type_selection()

    @api.model
    def _get_default_picking_type(self):
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)])
        return warehouse and warehouse[0].out_type_id or None

    carrier_type = fields.Selection(
        '_get_carrier_type_selection', string='Delivery Method Type',
        required=True, help="Carrier type (combines several delivery "
        "methods). Make sure that the option 'Deposit Slip' is checked on "
        "the delivery methods that have this carrier type.")
    picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Picking Type',
        required=True,
        default=_get_default_picking_type)

    @api.model
    def _prepare_deposit_slip(self):
        return {
            'carrier_type': self.carrier_type,
            'company_id': self.env.user.company_id.id,
            'picking_type_id': self.picking_type_id.id,
        }

    @api.model
    def _get_deposit_pickings(self):
        return self.env['stock.picking'].search([
            ('carrier_type', '=', self.carrier_type),
            ('deposit_slip_id', '=', False),
            ('state', '=', 'done'),
            ('picking_type_id', '=', self.picking_type_id.id),
        ])

    @api.multi
    def create_deposit_slip(self):
        # I can't set api.one because I return an action
        self.ensure_one()
        pickings = self._get_deposit_pickings()
        if pickings:
            vals = self._prepare_deposit_slip()
            deposit = self.env['deposit.slip'].create(vals)
            pickings.write({'deposit_slip_id': deposit.id})
            action = {
                'name': 'Deposit Slip',
                'type': 'ir.actions.act_window',
                'res_model': 'deposit.slip',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_id': deposit.id,
                'nodestroy': False,
                'target': 'current',
            }
            return action
        else:
            raise Warning(
                _("There are no delivery orders in transferred "
                    "state with a delivery method type '%s' "
                    "not already linked to a deposit slip.")
                % self.carrier_type)
