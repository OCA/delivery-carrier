from odoo import models, fields


class PackageDetails(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("dhl_parcel_de_provider", "DHL Parcel DE")],
        ondelete={"dhl_parcel_de_provider": "set default"},
    )
