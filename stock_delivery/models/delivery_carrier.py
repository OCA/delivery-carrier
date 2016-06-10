# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    delivery_type = fields.Selection(
        selection_add=[
            ('auto', 'Automatic'),
        ],
    )
