# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _is_residential_address(self):
        """Determine if the address is residential based on
        partner type and relationship
        """
        # Case 1: Individual with no company name
        if self.is_company and self.company_name:
            return False

        # Case 2: Private address of a parent partner
        if not self.parent_id or self.type == "other":
            return True

        # Case 3: If the recipient has a parent contact and
        # if the parent contact is residential
        if self.parent_id:
            return self.parent_id._is_residential_address()

        # Otherwise, it's a commercial address
        return False
