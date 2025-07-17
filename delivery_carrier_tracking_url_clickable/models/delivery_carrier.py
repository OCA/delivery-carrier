# Copyright - 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    tracking_number_separator = fields.Char(
        help="In case there exist multiple tracking numbers in carrier_tracking_ref, "
        "use this field to create separate urls."
    )
