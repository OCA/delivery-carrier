# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    theoretical_number_of_packages = fields.Integer(
        "Theoretical number of packages in a picking out",
        compute="_compute_theoretical_number_of_packages",
    )
    number_of_packages_done = fields.Integer(
        "Number of packages in a picking out",
        compute="_compute_number_of_packages_done",
    )
    is_number_of_packages_visible = fields.Boolean(
        "Number of packages visible",
        compute="_compute_is_number_of_packages_visible",
    )
    is_number_of_packages_outranged = fields.Boolean(
        "Too many packages compared to the theoretical number",
        compute="_compute_is_number_of_packages_outranged",
    )

    @api.depends(
        "picking_type_code", "carrier_id", "carrier_id.maximum_weight_per_package"
    )
    def _compute_is_number_of_packages_visible(self):
        for rec in self:
            if (
                rec.picking_type_code == "outgoing"
                and rec.carrier_id.maximum_weight_per_package
            ):
                rec.is_number_of_packages_visible = True
            else:
                rec.is_number_of_packages_visible = False

    @api.depends("is_number_of_packages_visible", "move_ids")
    def _compute_theoretical_number_of_packages(self):
        for rec in self:
            if rec.is_number_of_packages_visible:
                products_weights = rec.move_ids.mapped("product_id.weight")
                number_of_items = rec.move_ids.mapped("product_uom_qty")
                rec.theoretical_number_of_packages = rec._number_of_packages(
                    products_weights,
                    number_of_items,
                    rec.carrier_id.maximum_weight_per_package,
                )
            else:
                rec.theoretical_number_of_packages = False

    @api.depends(
        "is_number_of_packages_visible",
        "move_line_ids",
        "move_line_ids.result_package_id",
    )
    def _compute_number_of_packages_done(self):
        for rec in self:
            if rec.is_number_of_packages_visible:
                rec.number_of_packages_done = len(
                    rec.mapped("move_line_ids.result_package_id")
                )
            else:
                rec.number_of_packages_done = False

    @api.depends("theoretical_number_of_packages", "number_of_packages_done")
    def _compute_is_number_of_packages_outranged(self):
        for rec in self:
            if rec.is_number_of_packages_visible:
                rec.is_number_of_packages_outranged = (
                    rec.number_of_packages_done > rec.theoretical_number_of_packages
                )
            else:
                rec.is_number_of_packages_outranged = False

    def _number_of_packages(
        self, products_weights, number_of_items, maximum_weight_per_package
    ):
        # Split the product_weights into as many items as we haves
        products_weights_list = []
        for weight, number in zip(products_weights, number_of_items, strict=False):
            for _i in range(int(number)):
                products_weights_list.append(weight)

        products_weights_list.sort()

        i = 0
        weight = 0
        j = len(products_weights_list) - 1
        theoretical_number_of_packages = 0
        while i <= j:
            theoretical_number_of_packages += 1
            # Try to fit the heaviest product with the lightest.
            # If it does not work, then the heaviest should have
            # a box to itself
            weight = products_weights_list[i] + products_weights_list[j]
            while weight <= maximum_weight_per_package:
                i += 1
                if i < j:
                    # While the weight of products does not exceed the limit,
                    # continue adding products in the same package
                    weight += products_weights_list[i]
                else:
                    break

            j -= 1

        return theoretical_number_of_packages
