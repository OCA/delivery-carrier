from odoo import fields, models


class PackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("easypost_oca", "Easypost OCA")]
    )
    easypost_oca_carrier = fields.Char("Carrier Prefix", index=True)
