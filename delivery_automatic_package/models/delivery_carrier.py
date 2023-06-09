# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    automatic_package_creation_at_delivery = fields.Boolean(
        default=lambda self: self.env.company.automatic_package_creation_at_delivery_default,
        help="Check this in order to create automatically the delivery "
        "packages. Any lines not in a package will automaticaly be packaged.",
    )
    automatic_package_creation_mode = fields.Selection(
        [("single", "Single Package"), ("packaging", "Per Smallest Packaging")],
        required=True,
        default="single",
    )
