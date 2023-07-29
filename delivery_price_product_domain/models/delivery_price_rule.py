from odoo import models, fields

class DeliverPriceRule(models.Model):
    _inherit = "delivery.price.rule"

    exclude_product_domain = fields.Char(string="Ecxlude Products")