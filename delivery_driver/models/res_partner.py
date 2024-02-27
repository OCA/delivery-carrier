# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_driver = fields.Boolean("Driver")

    @api.constrains("is_driver")
    def _check_is_driver(self):
        drivers_in_carrier = self.env["delivery.carrier"].search(
            [("driver_id", "in", self.ids)]
        )
        if drivers_in_carrier and not self.is_driver:
            raise ValidationError(
                _(
                    "You can't remove the driver flag from a partner that"
                    " is set as driver in a delivery method."
                )
            )

    def _get_name(self):
        """When you see the driver in a list view, the display name is too long.
        With this you can see only the name"""
        if self.env.context.get("show_driver"):
            name = self.name or ""
            return f"{name}"
        return super()._get_name()
