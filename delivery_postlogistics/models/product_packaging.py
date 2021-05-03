# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(
        selection_add=[("postlogistics", "PostLogistics")]
    )

    def _get_packaging_codes(self):
        """
        Return the list of packaging codes
        """
        self.ensure_one()
        return [code.strip() for code in self.shipper_package_code.split(",")]
