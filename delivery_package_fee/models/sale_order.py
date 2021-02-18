# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_fee_line_qty_from_out_package(self, package_fee, picking, package):
        """Compute the fee qty for the package to deliver.

        Return 1 by default.
        """
        return 1

    def _package_fee_line_qty_and_price(self, package_fee, picking):
        fee_product = package_fee.product_id

        # line units
        out_packages = picking.mapped("move_line_ids.result_package_id")
        qty = sum(
            self._get_fee_line_qty_from_out_package(package_fee, picking, package)
            for package in out_packages
        )
        if not qty:
            return 0, 0.0

        # amount
        product = fee_product.with_context(
            pricelist=self.pricelist_id.id,
            partner=self.partner_id,
            quantity=qty,
            date=self.date_order,
            uom=fee_product.uom_id.id,
        )
        price_unit = self.currency_id._convert(
            product.price,
            self.company_id.currency_id,
            self.company_id,
            self.date_order or fields.Date.today(),
        )
        return qty, price_unit

    def _prepare_package_fee_line(self, package_fee, picking, qty, price_unit):
        # read fees details in the customer language
        package_fee = package_fee.with_context(lang=self.partner_id.lang)
        fee_product = package_fee.product_id

        # Apply fiscal position
        taxes = fee_product.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id
        )
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(
                taxes, fee_product, self.partner_id
            ).ids

        # line description
        if fee_product.description_sale:
            so_description = "{}: {}".format(
                fee_product.name, fee_product.description_sale
            )
        else:
            so_description = fee_product.name
        so_description = "{} ({})".format(so_description, picking.name)

        values = {
            "order_id": self.id,
            "name": so_description,
            "product_uom_qty": qty,
            "product_uom": fee_product.uom_id.id,
            "product_id": fee_product.id,
            "tax_id": [(6, 0, taxes_ids)],
            "price_unit": price_unit,
            "package_fee_id": package_fee.id,
        }
        if self.order_line:
            values["sequence"] = self.order_line[-1].sequence + 1
        return values

    def _create_package_fee_line(self, package_fee, picking):
        line_model = self.env["sale.order.line"].sudo()
        qty, price_unit = self._package_fee_line_qty_and_price(package_fee, picking)
        if not qty or self.currency_id.is_zero(price_unit):
            return line_model.browse()

        values = self._prepare_package_fee_line(package_fee, picking, qty, price_unit)
        return line_model.create(values)

    def copy_data(self, default=None):
        result = super().copy_data(default=default)
        new_result = []
        for values in result:
            # "sale" module sets this key
            if "order_line" in values:
                # remove package fee lines
                order_lines = [
                    line
                    for line in values["order_line"]
                    # lines are (0, 0, {}) commands
                    if not line[2].get("package_fee_id")
                ]
                values["order_line"] = order_lines
            new_result.append(values)
        return new_result
