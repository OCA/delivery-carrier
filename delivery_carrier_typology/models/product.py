# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    prohibited_shipping_means_ids = fields.Many2many(
        "delivery.carrier.typology",
        string="Prohibited shipping means",
    )

    computed_prohibited_shipping_means_ids = fields.Many2many(
        "delivery.carrier.typology", compute="_compute_prohibited_shipping_means_ids"
    )

    def _compute_prohibited_shipping_means_ids(self):
        for product_template in self:
            product_template.computed_prohibited_shipping_means_ids = False
            product_template.product_variant_ids._propagate_prohibited_shipping_means()


class ProductProduct(models.Model):
    _inherit = "product.product"

    prohibited_shipping_means_ids = fields.Many2many(
        "delivery.carrier.typology",
        string="Prohibited shipping means",
    )

    def _propagate_prohibited_shipping_means(self):
        for product in self:
            product.computed_prohibited_shipping_means_ids = False
            if product.product_tmpl_id.prohibited_shipping_means_ids:
                product.prohibited_shipping_means_ids = (
                    product.product_tmpl_id.prohibited_shipping_means_ids
                )
