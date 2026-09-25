# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    restrict_zone_to_delivery_addresses = fields.Boolean(
        string="Restrict Delivery Zone to Delivery Addresses",
        default=False,
        help="When enabled, the Delivery Zone field is only visible on "
        "delivery-type addresses. Disable to show it on all partner types.",
    )
