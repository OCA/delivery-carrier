# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DeliveryCarrier(models.Model):

    _inherit = 'delivery.carrier'

    @api.model
    def _get_default_category_id(self):
        return self.env['delivery.carrier.category'].search([], limit=1)

    category_id = fields.Many2one(
        string='Category',
        comodel_name='delivery.carrier.category',
        index=True,
        ondelete='restrict',
        default=lambda self: self._get_default_category_id(),
    )
