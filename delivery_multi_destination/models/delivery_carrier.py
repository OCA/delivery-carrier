# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.tools import config


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    child_ids = fields.One2many(
        comodel_name="delivery.carrier", inverse_name="parent_id",
        string="Destination grid",
    )
    parent_id = fields.Many2one(
        comodel_name="delivery.carrier", string="Parent carrier",
    )
    destination_type = fields.Selection(
        selection=[
            ('one', 'One destination'),
            ('multi', 'Multiple destinations'),
        ],
        default="one", required=True,
    )

    @api.multi
    def verify_carrier(self, contact):
        test_condition = (config['test_enable'] and
                          not self.env.context.get('test_delivery_multi'))
        if test_condition or self.destination_type == 'one':
            return super(DeliveryCarrier, self).verify_carrier(contact)
        for subcarrier in self.child_ids:
            if super(DeliveryCarrier, subcarrier).verify_carrier(contact):
                return subcarrier
