# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("postlogistics", "PostLogistics")],
        ondelete={"postlogistics": "set default"},
    )

    def _get_shipper_package_code_list(self, deduplicate=True):
        """
        Return the list of packaging codes, stripped and sorted.
        If deduplicate is True, the list is deduplicated.
        """
        self.ensure_one()
        if self.shipper_package_code and self.package_carrier_type == "postlogistics":
            shipper_package_codes = [
                code.strip() for code in self.shipper_package_code.split(",")
            ]
            if deduplicate:
                shipper_package_codes = set(shipper_package_codes)
            return list(sorted(shipper_package_codes))
        return []
