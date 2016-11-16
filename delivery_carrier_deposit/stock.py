# -*- encoding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2012-2014 Akretion France (www.akretion.com)
#   @author: David BEAL <david.beal@akretion.com>
#   @author: Sebastien BEAU <sebastien.beau@akretion.com>
#   @author: Benoit GUILLOT <benoit.guillot@akretion.com>
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

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class DepositSlip(models.Model):
    _name = 'deposit.slip'
    _description = 'Deposit Slip'
    _order = 'id desc'
    _inherit = ['mail.thread']
    _track = {
        'state': {
            'delivery_carrier_deposit.deposit_slip_done':
            lambda self, cr, uid, obj, ctx=None: obj.state == 'done',
            }
        }

    @api.one
    @api.depends('picking_ids')
    def _compute_deposit_slip(self):
        weight = 0.0
        number_of_packages = 0
        for picking in self.picking_ids:
            number_of_packages += picking.number_of_packages
            weight += picking.weight
        self.weight = weight
        self.number_of_packages = number_of_packages

    @api.model
    def _get_carrier_type_selection(self):
        return self.env['delivery.carrier']._get_carrier_type_selection()

    name = fields.Char(
        readonly=True, states={'draft': [('readonly', False)]},
        default='/', copy=False)
    carrier_type = fields.Selection(
        '_get_carrier_type_selection', string='Type',
        readonly=True, required=True, copy=False,
        help="Carrier type (combines several delivery methods)")
    picking_ids = fields.One2many(
        'stock.picking', 'deposit_slip_id', string='Pickings',
        readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], string='Status', readonly=True, default='draft')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'deposit.slip'))
    weight = fields.Float(
        string='Total Weight', compute='_compute_deposit_slip',
        digits=dp.get_precision('Stock Weight'), readonly=True)
    number_of_packages = fields.Integer(
        string='Number of Packages', compute='_compute_deposit_slip',
        readonly=True)
    picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string='Picking Type',
        required=True)

    _sql_constraints = [(
        'name_company_uniq',
        'unique(name, company_id)',
        "'Deposit Slip' name must be unique per company!")]

    @api.model
    def create(self, vals=None):
        if vals is None:
            vals = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'delivery.deposit')
        return super(DepositSlip, self).create(vals)

    @api.multi
    def create_edi_file(self):
        """
        Override this method for the proper carrier
        """
        return True

    @api.multi
    def validate_deposit(self):
        self.create_edi_file()
        self.write({'state': 'done'})
        return True


class StockPicking(models.Model):
    _inherit = "stock.picking"

    deposit_slip_id = fields.Many2one('deposit.slip', 'Deposit Slip')


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    deposit_slip = fields.Boolean(
        string='Deposit Slip',
        help="Allow to create a 'Deposit Slip' report on delivery orders")
