# Copyright 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    @api.model
    def _get_delivery_partner_from_purchase(self, purchase):
        return purchase.dest_address_id or purchase.partner_id

    def purchase_rate_shipment(self, order):
        """Compute the price of the order shipment

        :param order: record of purchase.order
        :return dict: {'success': boolean,
                       'price': a float,
                       'error_message': a string containing an error message,
                       'warning_message': a string containing a warning message}
        """
        self.ensure_one()
        if hasattr(self, "purchase_%s_rate_shipment" % self.delivery_type):
            res = getattr(self, "purchase_%s_rate_shipment" % self.delivery_type)(order)
            # apply margin on computed price
            res["price"] = float(res["price"]) * (1.0 + (self.margin / 100.0))
            # save the real price in case a free_over rule overide it to 0
            res["carrier_price"] = res["price"]
            # free when order is large enough
            if (
                res["success"]
                and self.free_over
                and (order.amount_total + order.delivery_price) >= self.amount
            ):
                res["warning_message"] = _(
                    "The shipping is free since the order amount exceeds %.2f."
                ) % (self.amount)
                res["price"] = 0.0
            return res

    def purchase_send_shipping(self, pickings):
        """Send the package to the service provider

        :param pickings: A recordset of pickings
        :return list: A list of dictionaries (one per picking) containing of the form::
                         { 'exact_price': price,
                           'tracking_number': number }
        """
        self.ensure_one()
        if hasattr(self, "purchase_%s_send_shipping" % self.delivery_type):
            return getattr(self, "purchase_%s_send_shipping" % self.delivery_type)(
                pickings
            )

    def purchase_fixed_rate_shipment(self, order):
        carrier = self._match_address(order.partner_id)
        if not carrier:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "Error: this delivery method is not available for this address."
                ),
                "warning_message": False,
            }
        price = self.fixed_price
        company = self.company_id or order.company_id or self.env.company
        if company.currency_id != order.currency_id:
            price = company.currency_id._convert(
                price, order.currency_id, company, fields.Date.today()
            )
        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }

    def purchase_base_on_rule_rate_shipment(self, order):
        carrier = self._match_address(order.partner_id)
        if not carrier:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _("Error: no matching grid."),
                "warning_message": False,
            }

        try:
            price_unit = self._purchase_get_price_available(order)
        except UserError as e:
            return {
                "success": False,
                "price": 0.0,
                "error_message": e.name,
                "warning_message": False,
            }
        if order.company_id.currency_id.id != order.currency_id.id:
            price_unit = order.company_id.currency_id._convert(
                price_unit,
                order.currency_id,
                order.company_id,
                order.date_order or fields.Date.today(),
            )

        return {
            "success": True,
            "price": price_unit,
            "error_message": False,
            "warning_message": False,
        }

    def purchase_fixed_send_shipping(self, pickings):
        res = []
        for p in pickings:
            res = res + [
                {"exact_price": p.carrier_id.fixed_price, "tracking_number": False}
            ]
        return res

    def purchase_base_on_rule_send_shipping(self, pickings):
        res = []
        for p in pickings:
            carrier = self._match_address(p.partner_id)
            if not carrier:
                raise ValidationError(_("There is no matching delivery rule."))
            res = res + [
                {
                    "exact_price": p.carrier_id._purchase_get_price_available(
                        p.purchase_id
                    )
                    if p.purchase_id
                    else 0.0,
                    "tracking_number": False,
                }
            ]
        return res

    def _purchase_get_price_available(self, order):
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        weight = volume = quantity = 0
        for line in order.order_line.filtered(
            lambda l: l.state != "cancel" and bool(l.product_id)
        ):
            qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total = order.amount_total or 0.0
        total = order.currency_id._convert(
            total,
            order.company_id.currency_id,
            order.company_id,
            order.date_order or fields.Date.today(),
        )
        return self._get_price_from_picking(total, weight, volume, quantity)
