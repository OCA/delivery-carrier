# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _is_ups_residential_address(self):
        """Determine if the address is residential based on
        partner type and parent.
        """
        if self.is_company and self.company_name:
            return False
        if not self.parent_id or self.type == "other":
            return True
        if self.parent_id:
            return self.parent_id._is_ups_residential_address()
        return False
