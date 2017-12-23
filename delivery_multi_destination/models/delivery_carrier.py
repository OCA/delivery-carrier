# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Don't show by default children carriers."""
        if not self.env.context.get('show_children_carriers'):
            if args is None:
                args = []
            args += [('parent_id', '=', False)]
        return super(DeliveryCarrier, self).search(
            args, offset=offset, limit=limit, order=order, count=count,
        )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Don't show by default children carriers."""
        if not self.env.context.get('show_children_carriers'):
            if args is None:
                args = []
            args += [('parent_id', '=', False)]
        return super(DeliveryCarrier, self)._name_search(
            name=name, args=args, operator=operator, limit=limit,
        )

    @api.multi
    def verify_carrier(self, contact):
        if self.destination_type == 'one':
            return super(DeliveryCarrier, self).verify_carrier(contact)
        carrier = self.with_context(show_children_carriers=True)
        for subcarrier in carrier.child_ids:
            if super(DeliveryCarrier, subcarrier).verify_carrier(contact):
                return subcarrier
