# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("test", "Test")], ondelete={"test": "cascade"}
    )
