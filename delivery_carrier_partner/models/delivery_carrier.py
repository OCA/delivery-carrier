# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Carrier(models.Model):
    _inherit = 'delivery.carrier'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        help='The partner that is doing the delivery service.',
        string='Transporter')
