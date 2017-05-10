# -*- coding: utf-8 -*-
#   Copyright (C) 2012-2014 Akretion France (www.akretion.com)
#   @author: David BEAL <david.beal@akretion.com>
#   @author: Sebastien BEAU <sebastien.beau@akretion.com>
#   @author: Chafique DELLI <chafique.delli@akretion.com>
#   @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _
from odoo.exceptions import Warning


class DeliveryDepositWizard(models.TransientModel):
    _name = "delivery.deposit.wizard"
    _description = "Wizard to create Deposit Slip"
    _rec_name = 'carrier_type'

    @api.model
    def _get_carrier_type_selection(self):
        return self.env['delivery.carrier']._get_carrier_type_selection()

    carrier_type = fields.Selection(
        '_get_carrier_type_selection', string='Delivery Method Type',
        required=True, help="Carrier type (combines several delivery "
        "methods). Make sure that the option 'Deposit Slip' is checked on "
        "the delivery methods that have this carrier type.")

    @api.model
    def _prepare_deposit_slip(self):
        return {
            'carrier_type': self.carrier_type,
            'company_id': self.env.user.company_id.id,
            }

    @api.multi
    def create_deposit_slip(self):
        # I can't set api.one because I return an action
        self.ensure_one()
        pickings = self.env['stock.picking'].search([
            ('carrier_type', '=', self.carrier_type),
            ('deposit_slip_id', '=', False),
            ('state', '=', 'done'),
            ])
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
