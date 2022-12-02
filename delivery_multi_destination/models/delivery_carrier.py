# Copyright 2016-2020 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2021 Gianmarco Conte <gconte@dinamicheaziendali.it>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    child_ids = fields.One2many(
        comodel_name="delivery.carrier",
        inverse_name="parent_id",
        string="Destination grid",
    )
    parent_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Parent carrier",
        ondelete="cascade",
    )
    destination_type = fields.Selection(
        selection=[("one", "One destination"), ("multi", "Multiple destinations")],
        default="one",
        required=True,
    )

    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Don't show by default children carriers."""
        if not self.env.context.get("show_children_carriers"):
            if args is None:
                args = []
            args += [("parent_id", "=", False)]
        return super(DeliveryCarrier, self).search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            count=count,
        )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Don't show by default children carriers."""
        domain = [("parent_id", "=", False)]
        return self.search(domain, limit=limit).name_get()

    def available_carriers(self, partner):
        """If the carrier is multi, we test the availability on children."""
        available = self.env["delivery.carrier"]
        for carrier in self:
            if carrier.destination_type == "one":
                candidates = carrier
            else:
                carrier = carrier.with_context(show_children_carriers=True)
                candidates = carrier.child_ids
            if super(DeliveryCarrier, candidates).available_carriers(partner):
                available |= carrier
        return available

    def rate_shipment(self, order):
        """We have to override this method for getting the proper price
        according destination on sales orders.
        """
        if self.destination_type == "one":
            return super().rate_shipment(order)
        else:
            carrier = self.with_context(show_children_carriers=True)
            for subcarrier in carrier.child_ids:
                if subcarrier._match_address(order.partner_shipping_id):
                    return super(
                        DeliveryCarrier,
                        subcarrier,
                    ).rate_shipment(order)

    def send_shipping(self, pickings):
        """We have to override this method for redirecting the result to the
        proper "child" carrier.
        """
        # falsy type is considered as one destination
        if not self.destination_type or self.destination_type == "one":
            return super().send_shipping(pickings)
        carrier = self.with_context(show_children_carriers=True)
        res = []
        for p in pickings:
            picking_res = False
            for subcarrier in carrier.child_ids:
                picking_res = subcarrier._send_shipping_next(p, picking_res)
            if not picking_res:
                raise ValidationError(_("There is no matching delivery rule."))
            res += picking_res
        return res

    def _send_shipping_next(self, picking, picking_res):
        if self.delivery_type == "fixed":
            if self._match_address(picking.partner_id):
                picking_res = [
                    {
                        "exact_price": self.fixed_price,
                        "tracking_number": False,
                    }
                ]
            # TODO: verify if not match address, previous picking_res (passed
            # in method's argument) can be used.
        else:
            try:
                picking_res = super().send_shipping(picking)
            except Exception as err:
                _logger.warning("%s: %s", "_send_shipping_next", str(err))
        return picking_res
