# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = 'delivery.carrier'

    partner_id = fields.Many2one(
        string='Transporter Company',
        comodel_name='res.partner',
        help='The partner that is doing the delivery service.'
    )
