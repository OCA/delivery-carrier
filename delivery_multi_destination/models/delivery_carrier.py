# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

    def available_carriers(self, partner):
        """Add childrens on the possible list to select carriers. This is
        used on `website_sale_delivery` module.
        """
        candidates = self.env['delivery.carrier']
        for carrier in self:
            if self.destination_type == 'one':
                candidates |= carrier
            else:
                carrier = self.with_context(show_children_carriers=True)
                candidates |= carrier.child_ids
        return super(DeliveryCarrier, candidates).available_carriers(partner)

    def rate_shipment(self, order):
        """We have to override this method for getting the proper price
        according destination on sales orders.
        """
        if self.destination_type == 'one':
            return super().rate_shipment(order)
        else:
            carrier = self.with_context(show_children_carriers=True)
            for subcarrier in carrier.child_ids:
                if subcarrier._match_address(order.partner_shipping_id):
                    return super(
                        DeliveryCarrier, subcarrier,
                    ).rate_shipment(order)
