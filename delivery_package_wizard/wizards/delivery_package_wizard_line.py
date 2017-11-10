# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class DeliveryPackageWizardLine(models.TransientModel):

    _name = 'delivery.package.wizard.line'

    wizard_id = fields.Many2one(
        string='Wizard',
        comodel_name='delivery.package.wizard',
        required=True,
        ondelete='cascade',
    )
    delivery_type = fields.Selection(
        string='Carrier',
        related='wizard_id.picking_id.carrier_id.delivery_type',
    )
    dispatch_package_id = fields.Many2one(
        string='Dispatch Package',
        comodel_name='product.packaging',
        required=True,
        domain="[('package_carrier_type', '=', delivery_type)]",
    )
    quant_package_id = fields.Many2one(
        string='Quant Package',
        comodel_name='stock.quant.package',
    )
