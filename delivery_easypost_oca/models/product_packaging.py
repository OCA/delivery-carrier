from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(
        selection_add=[("easypost_oca", "Easypost OCA")]
    )
    easypost_oca_carrier = fields.Char("Carrier Prefix", index=True)
