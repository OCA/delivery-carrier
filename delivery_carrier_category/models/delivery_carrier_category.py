# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrierCategory(models.Model):

    _name = 'delivery.carrier.category'
    _description = 'Delivery Carrier Category'
    _order = 'sequence, id'

    name = fields.Char(
        translate=True,
        required=True,
    )
    code = fields.Char(
        required=True,
    )
    sequence = fields.Integer(
        default=10,
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )

    _sql_constraints = [
        ('code_uniq',
         'EXCLUDE (code WITH =) WHERE (active = True)',
         'Each code must be unique.'),
    ]
