# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    carrier_ids = fields.One2many(
        "delivery.carrier",
        "driver_id",
        string="Delivery Carriers",
    )

    is_driver = fields.Boolean(
        string="Driver",
        compute="_compute_is_driver",
        store=True,
    )

    @api.depends("carrier_ids")
    def _compute_is_driver(self):
        for partner in self:
            partner.is_driver = bool(partner.carrier_ids)

    @api.constrains("is_driver")
    def _check_is_driver(self):
        drivers_in_carrier = self.env["delivery.carrier"].search(
            [("driver_id", "in", self.ids)]
        )
        if drivers_in_carrier and drivers_in_carrier.filtered_domain(
            [("driver_id.is_driver", "=", False)]
        ):
            raise ValidationError(
                self.env._(
                    "You can't remove the driver flag from a partner that"
                    " is set as driver in a delivery method."
                )
            )

    @api.depends("name")
    def _compute_display_name(self):
        """When you see the driver in a list view, the display name is too long.
        With this you can see only the name"""
        if self.env.context.get("show_driver"):
            for partner in self:
                partner.display_name = partner.name or ""
        else:
            return super()._compute_display_name()
