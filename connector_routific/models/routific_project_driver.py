# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class RoutificProjectDriver(models.Model):
    """Routifc creates new drivers for every project created."""

    _name = "routific.project.driver"
    _description = "Routific drivers for every project"

    driver_id = fields.Many2one(
        comodel_name="res.partner",
        string="Driver",
        required=True,
        domain=[
            ("is_routific_driver", "=", True),
            ("routific_driver_active", "=", True),
        ],
    )
    project_id = fields.Many2one(comodel_name="routific.project", string="Project")
    routific_driver_id = fields.Char()
