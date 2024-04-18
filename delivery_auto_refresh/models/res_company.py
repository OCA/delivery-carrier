# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Migration Note 17.0: move this to module sale_order_carrier_auto_assign
    sale_auto_assign_carrier_on_create = fields.Boolean(
        "Set default shipping method automatically"
    )
    # End migration note
