# Copyright 2016-2020 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2021 Gianmarco Conte <gconte@dinamicheaziendali.it>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    @api.onchange("destination_type", "child_ids")
    def _onchange_destination_type(self):
        """Define the corresponding value to avoid creation error with UX."""
        if self.destination_type == "multi" and self.child_ids and not self.product_id:
            self.product_id = fields.first(self.child_ids.product_id)

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Don't show by default children carriers."""
        if not self.env.context.get("show_children_carriers"):
            if domain is None:
                domain = []
            domain += [("parent_id", "=", False)]
        return super().search(domain, offset=offset, limit=limit, order=order)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Don't show by default children carriers."""
        args = args or []
        args += [("parent_id", "=", False)]
        return super().name_search(name, args, operator, limit)

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
        if self.destination_type == "one" or not self:
            return super().send_shipping(pickings)
        else:
            carrier = self.with_context(show_children_carriers=True)
            res = []
            for p in pickings:
                picking_res = False
                for subcarrier in carrier.child_ids.filtered(
                    lambda x, p=p: not x.company_id or x.company_id == p.company_id
                ):
                    if subcarrier.delivery_type == "fixed":
                        if subcarrier._match_address(p.partner_id):
                            picking_res = [
                                {
                                    "exact_price": subcarrier.fixed_price,
                                    "tracking_number": False,
                                }
                            ]
                            break
                    else:
                        try:
                            # on base_on_rule_send_shipping, the method
                            # _get_price_available is called using p.carrier_id,
                            # ignoring the self arg, so we need to temporarily replace
                            # it with the subcarrier
                            p.carrier_id = subcarrier.id
                            picking_res = super(
                                DeliveryCarrier, subcarrier
                            ).send_shipping(p)
                            break
                        except Exception:  # pylint: disable=except-pass
                            pass
                        finally:
                            p.carrier_id = carrier
                if not picking_res:
                    raise ValidationError(_("There is no matching delivery rule."))
                res += picking_res
            return res
