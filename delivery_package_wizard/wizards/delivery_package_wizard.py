# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class DeliveryPackageWizard(models.TransientModel):

    _name = 'delivery.package.wizard'

    picking_id = fields.Many2one(
        string='Picking',
        comodel_name='stock.picking',
        default=lambda s: s._default_picking_id(),
        readonly=True,
    )
    package_ids = fields.Many2many(
        string='Packages',
        compute='_compute_package_ids',
        comodel_name='stock.quant.package',
    )
    wizard_line_ids = fields.One2many(
        string='Packages',
        comodel_name='delivery.package.wizard.line',
        compute='_compute_wizard_line_ids',
        inverse_name='wizard_id',
    )

    @api.model
    def _default_picking_id(self):
        if self.env.context.get('active_model') == 'stock.picking':
            return self.env.context.get('active_id', False)

    @api.multi
    @api.depends('picking_id.package_ids')
    def _compute_package_ids(self):
        for record in self:
            packages = record.picking_id.package_ids.filtered(
                lambda r: not r.packaging_id
            )
            record.package_ids = [(6, 0, packages.ids)]

    @api.multi
    @api.depends('package_ids')
    def _compute_wizard_line_ids(self):
        for record in self:
            wizard_lines = self.env['delivery.package.wizard.line']
            for package in record.package_ids:
                wizard_lines += wizard_lines.create({
                    'wizard_id': record.id,
                    'quant_package_id': package.id,
                })
            record.wizard_line_ids = [(6, 0, wizard_lines.ids)]

    @api.multi
    def action_ship(self):
        self.ensure_one()
        for wizard_line in self.wizard_line_ids:
            dispatch_package = wizard_line.dispatch_package_id
            wizard_line.quant_package_id.packaging_id = dispatch_package.id
        return self.picking_id.with_context(force_send=True).send_to_shipper()

    @api.multi
    def action_show(self):
        action = self.get_formview_action()
        action.update({
            'target': 'new',
            'flags': {'initial_mode': 'edit'},
        })
        return action
