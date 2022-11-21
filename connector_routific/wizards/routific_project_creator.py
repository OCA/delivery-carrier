# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class RoutificProjectCreator(models.TransientModel):
    """Wizard launched from stock.pickings that allow us to create routific.project
    by selecting all the pickings that have to be delivered.
    """

    _name = "routific.project.creator"
    _description = "Wizard for Routific project creation"

    def _default_driver_ids(self):
        # By default we get all drivers.
        return self.env["res.partner"].search(
            [("is_routific_driver", "=", True), ("routific_driver_active", "=", True)]
        )

    def _default_config_id(self):
        return min(self.env["routific.config"].search([]), key=lambda rc: rc.sequence)

    driver_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Drivers",
        domain=[
            ("is_routific_driver", "=", True),
            ("routific_driver_active", "=", True),
        ],
        default=_default_driver_ids,
        required=True,
    )
    config_id = fields.Many2one(
        comodel_name="routific.config",
        string="Settings",
        required=True,
        default=_default_config_id,
    )
    date = fields.Date(
        string="Delivery date", default=date.today() + timedelta(days=1), required=True
    )

    def create_project(self):
        picking_ids = self.env["stock.picking"].browse(self.env.context["active_ids"])
        for picking in picking_ids:
            if picking.picking_type_id != self.config_id.picking_type_id:
                raise UserError(
                    _(
                        "The operation type %(picking_name)s is not allowed on "
                        "%(config_name)s configuration"
                    )
                    % {
                        "picking_name": picking.picking_type_id.name,
                        "config_name": self.config_id.name,
                    }
                )
            if picking.driver_id:
                raise UserError(
                    _("The picking %s has a driver assigned yet") % (picking.name)
                )
            if picking.state != "assigned":
                raise UserError(_("The picking %s is not Ready") % (picking.name))
        project = self.env["routific.project"].create(
            {
                "routific_config_id": self.config_id.id,
                "picking_ids": self.env.context["active_ids"],
                "project_driver_ids": [
                    (0, 0, {"driver_id": driver.id}) for driver in self.driver_ids
                ],
            }
        )
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "routific.project",
            "res_id": project.id,
            "type": "ir.actions.act_window",
            "context": {},
        }
