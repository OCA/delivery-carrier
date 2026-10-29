# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import config, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _skip_remove_create_delivery_line(self):
        """This method allows you to decide when to exclude remove or create delivery
        lines; for example, when the delivery line has already been invoiced and you
        want to change the shipment WITHOUT changing the price.
        """
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_delivery_order_switch_carrier")
        )
        if not test_condition:
            return False
        if not self.env.context.get("from_choose_delivery_carrier"):
            return False
        delivery_lines = self.order_line.filtered("is_delivery")
        if not delivery_lines:
            return False
        to_delete = delivery_lines.filtered(lambda x: x.qty_invoiced == 0)
        if to_delete:
            return False
        delivery_price = self.env.context.get("choose_delivery_carrier_price")
        delivery_lines_price = sum(delivery_lines.mapped("price_unit"))
        dp = self.env["decimal.precision"].precision_get("Product Price")
        if (
            float_compare(delivery_lines_price, delivery_price, precision_digits=dp)
            == 0
        ):
            return True
        return False

    def _remove_delivery_line(self):
        if self._skip_remove_create_delivery_line():
            return
        return super()._remove_delivery_line()

    def _prepare_update_delivery_line_vals(self, carrier, price_unit):
        line_vals = self._prepare_delivery_line_vals(carrier, price_unit)
        return {
            "name": line_vals["name"],
        }

    def _update_delivery_line(self, carrier, price_unit):
        """This method will update the existing delivery line and the associated
        invoice lines.
        This change is made to reflect the actual situation (Shipping Method A was
        initially specified, and the invoice was created accordingly, but it was
        later changed to Shipping Method B).
        """
        delivery_lines = self.order_line.filtered("is_delivery")
        if delivery_lines:
            delivery_line = fields.first(delivery_lines)
            vals = self._prepare_update_delivery_line_vals(carrier, price_unit)
            delivery_line.write(vals)
            if delivery_line.invoice_lines:
                delivery_line.invoice_lines.write(vals)

    def _create_delivery_line(self, carrier, price_unit):
        if self._skip_remove_create_delivery_line():
            self._update_delivery_line(carrier, price_unit)
            return
        return super()._create_delivery_line(carrier, price_unit)
