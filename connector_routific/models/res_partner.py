# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.phone_validation.tools.phone_validation import phone_format
from odoo.addons.resource.models.resource import float_to_time


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_routific_driver = fields.Boolean(string="Is driver", company_dependent=True)
    routific_driver_active = fields.Boolean(
        string="Driver active",
        company_dependent=True,
        compute="_compute_routific_active",
        readonly=False,
        store=True,
    )
    partner_start_id = fields.Many2one(
        comodel_name="res.partner", string="Start location"
    )
    partner_end_id = fields.Many2one(comodel_name="res.partner", string="End location")
    finish_at_start = fields.Boolean(
        string="Finish route where start", default=True, company_dependent=True
    )
    routific_start = fields.Float(
        string="Start",
        company_dependent=True,
        help="""
        If the partner is a driver, this value shows the start work schedule.
        If it isn't it will show the start of the time that can receive a shipping.
        """,
    )
    routific_end = fields.Float(
        string="End",
        default=24.0,
        company_dependent=True,
        help="""
        If the partner is a driver, this value shows the end work schedule.
        If it isn't it will show the end of the time that can receive a shipping.
        """,
    )
    delivery_duration = fields.Integer(string="Delivery duration (MIN)")
    speed = fields.Float(
        default=1.0,
        help="""Set the average speed of the driver
        being 0.1 the smallest and 2.0 the biggest""",
    )
    capacity = fields.Integer(
        company_dependent=True,
        help="Keep as 0 for no control of capacity",
    )
    routific_type_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        string="Types allowed",
        domain="[('id', '=', allowed_routific_type_ids)]",
    )
    allowed_routific_type_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        compute="_compute_allowed_routific_type_ids",
    )

    def _compute_routific_active(self):
        """Method to be extended in possible extra modules"""

    def get_address(self, address_format="", partner_id=False):
        """With this method we achieve to calculate the address that has to be sent to
        Routific API.
        """
        args = {
            "street": partner_id.street or "",
            "city": partner_id.city or "",
            "state": partner_id.state_id.name or "",
            "zip": partner_id.zip or "",
            "country": partner_id.country_id.name or "",
        }
        return address_format % args

    def get_routific_data(self, config_id):
        """With this method we build the diccionary of one driver that has to be sent
        to Routific.
        """
        vals = {
            "name": "{} [{}]".format(self.name, self.id),
            "start_location": {
                "address": self.get_address(
                    address_format=config_id.address_format,
                    partner_id=self.partner_start_id,
                )
            },
            "speed": self.speed,
            "types": self.routific_type_ids.mapped("name"),
        }
        if self.routific_start != 0.0:
            vals["shift_start"] = float_to_time(self.routific_start).strftime("%H:%M")
        if self.routific_end != 24.0:
            vals["shift_end"] = float_to_time(self.routific_end).strftime("%H:%M")
        phone = self.get_formatted_mobile_or_phone()
        if phone:
            vals["phone_number"] = phone
        if self.finish_at_start:
            vals["end_location"] = vals["start_location"]
        elif self.partner_end_id:
            vals["end_location"] = {
                "address": self.get_address(
                    address_format=config_id.address_format,
                    partner_id=self.partner_end_id,
                )
            }
        if self.capacity:
            vals["capacity"] = self.capacity
        return vals

    @api.depends("company_id")
    def _compute_allowed_routific_type_ids(self):
        """This method give us the allowed product.attribute.values that can be
        selected on routific_type_ids field.
        """
        for record in self:
            attributes = self.env["product.attribute"].search(
                [("is_routific_type", "=", True)]
            )
            record.allowed_routific_type_ids = attributes.mapped(
                "attribute_line_ids.value_ids"
            )

    @api.constrains("speed")
    def _check_range_speed_value(self):
        for ref in self:
            if ref.speed < 0.1 or ref.speed > 2.0:
                raise UserError(
                    _("The speed of the driver must be a value between 0.1 and 2.0")
                )

    @api.constrains("routific_start", "routific_end")
    def _check_time_values(self):
        for ref in self:
            if ref.routific_start >= ref.routific_end:
                raise UserError(_("The start of the schedule must be before the end"))
            if ref.routific_start < 0.0:
                raise UserError(_("The day starts at 00:00"))
            if ref.routific_end > 24.0:
                raise UserError(_("The day ends at 24:00"))

    def get_formatted_mobile_or_phone(self):
        phone = self.mobile or self.phone
        country = self.country_id or self.env.company.country_id
        if phone:
            try:
                phone = phone_format(
                    phone,
                    country.code if country else None,
                    country.phone_code if country else None,
                    force_format="INTERNATIONAL",
                    raise_exception=True,
                )
            except Exception:
                phone = False
        return phone
