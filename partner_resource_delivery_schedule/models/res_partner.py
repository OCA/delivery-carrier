# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_schedule_resource_id = fields.Many2one(
        comodel_name="resource.resource",
        string="Delivery Schedule Resource",
        domain=[("resource_type", "=", "delivery")],
        readonly=True,
    )
    delivery_schedule_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        string="Delivery Schedule Calendar",
        compute="_compute_delivery_schedule_calendar_id",
        inverse="_inverse_delivery_schedule_calendar_id",
        domain=[("is_delivery_schedule", "=", True)],
        compute_sudo=True,
        store=True,
        tracking=True,
    )

    def action_create_delivery_schedule_resource(self):
        """Create a delivery schedule resource for the partner."""
        for record in self:
            if record.delivery_schedule_resource_id:
                continue
            record.delivery_schedule_resource_id = (
                self.env["resource.resource"]
                .sudo()
                .create(
                    {
                        "name": f"[{_('Delivery Schedule')}] {record.display_name}",
                        "resource_type": "delivery",
                        "company_id": record.company_id.id,
                    }
                )
            )

    @api.depends("delivery_schedule_resource_id.calendar_id")
    def _compute_delivery_schedule_calendar_id(self):
        """Get the calendar associated to the schedule resource"""
        for record in self:
            record.delivery_schedule_calendar_id = (
                record.delivery_schedule_resource_id.calendar_id
            )

    def _inverse_delivery_schedule_calendar_id(self):
        """Set the calendar on the associated schedule resource or remove the resource
        if no calendar is set. Resources must have an associated calendar."""
        for record in self:
            if not record.delivery_schedule_calendar_id:
                record.delivery_schedule_resource_id.sudo().unlink()
                continue
            # Resource exists > update calendar
            if not record.delivery_schedule_resource_id:
                record.action_create_delivery_schedule_resource()
            record.sudo().delivery_schedule_resource_id.calendar_id = (
                record.delivery_schedule_calendar_id
            )
