# Copyright 2026 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PackageType(models.Model):
    _inherit = "stock.package.type"

    allowed_package_carrier_ids = fields.Many2many(
        "delivery.carrier",
        string="Delivery Methods",
        help="Restrict this package type to listed delivery methods. When empty, it"
        " will be available to all delivery methods of the carrier",
    )
