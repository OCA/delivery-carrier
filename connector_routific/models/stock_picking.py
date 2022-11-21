# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from email_validator import validate_email

from odoo import fields, models

from odoo.addons.resource.models.resource import float_to_time


class StockPicking(models.Model):
    _inherit = "stock.picking"

    driver_id = fields.Many2one(comodel_name="res.partner", string="Driver")
    routific_stop_id = fields.Char(string="Routific stop id")
    routific_project_id = fields.Many2one(
        comodel_name="routific.project", string="Routific project id"
    )
    routific_stop_sequence = fields.Integer(string="Sequence stop")

    def get_routific_data(self, config_id):
        """With this method we build the diccionary of one stop that has to be sent
        to Routific.
        """
        vals = {
            "name": self.partner_id.name,
            "location": {
                "address": self.partner_id.get_address(
                    address_format=config_id.address_format, partner_id=self.partner_id
                )
            },
            "types": self._get_product_types().mapped("name"),
            "custom_notes": {"picking_id": "%s" % self.id},
        }
        if self.partner_id.routific_start != 0.0:
            vals["start"] = float_to_time(self.partner_id.routific_start).strftime(
                "%H:%M"
            )
        if self.partner_id.routific_end != 24.0:
            vals["end"] = float_to_time(self.partner_id.routific_end).strftime("%H:%M")
        # Compute mobile/phone for avoid send unformatted values
        phone = self.partner_id.get_formatted_mobile_or_phone()
        if phone:
            vals["phone_number"] = phone
        # Validate email for avoid send incorrect values
        try:
            email = validate_email(
                self.partner_id.email, check_deliverability=False
            ).email
        except Exception:
            email = False
        if email:
            vals["email"] = email
        if self.partner_id.delivery_duration:
            vals["duration"] = self.partner_id.delivery_duration
        if self.note:
            vals["notes"] = self.note
        return vals

    def _get_product_types(self):
        """Method to get the afected types of products on a picking."""
        attribute_value_ids = self.env["product.attribute.value"]
        for product in self.move_lines.mapped("product_id"):
            for tmpl_attribute_value in product.product_template_attribute_value_ids:
                if tmpl_attribute_value.attribute_id.is_routific_type:
                    attribute_value_ids += (
                        tmpl_attribute_value.product_attribute_value_id
                    )
        return attribute_value_ids
