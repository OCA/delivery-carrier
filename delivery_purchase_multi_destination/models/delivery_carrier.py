# Copyright 2025 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def purchase_rate_shipment(self, order):
        # We have to override this method for getting the proper price
        # according destination on purchase orders.
        if self.destination_type == "one":
            return super().purchase_rate_shipment(order)
        else:
            carrier = self.with_context(show_children_carriers=True)
            for subcarrier in carrier.child_ids:
                if subcarrier._match_address(order.partner_id):
                    return super(
                        DeliveryCarrier,
                        subcarrier,
                    ).purchase_rate_shipment(order)
            raise ValidationError(_("There is no matching delivery rule."))

    def purchase_send_shipping(self, pickings):
        # We have to override this method for redirecting the result to the
        # proper "child" carrier.
        if self.destination_type == "one" or not self:
            return super().purchase_send_shipping(pickings)
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
                            ).purchase_send_shipping(p)
                            break
                        except Exception:  # pylint: disable=except-pass
                            # If the subcarrier does not match the partner address,
                            # a “no matching rule” exception is raised,
                            # so we need to check the remaining subcarriers.
                            pass
                        finally:
                            p.carrier_id = carrier
                if not picking_res:
                    # If there is no picking_res, it means there is no subcarrier,
                    # so raise a ValidationError to inform the user about the issue.
                    # This prevents a subsequent error when trying to access a null
                    # value.
                    raise ValidationError(_("There is no matching delivery rule."))
                res += picking_res
            return res
