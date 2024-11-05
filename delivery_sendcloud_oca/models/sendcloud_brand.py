# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, fields, models


class SendcloudBrand(models.Model):
    _name = "sendcloud.brand"
    _inherit = ["sendcloud.mixin"]
    _description = "Sendcloud Brand"

    name = fields.Char(required=True)
    sendcloud_code = fields.Integer(required=True)
    color = fields.Char()
    secondary_color = fields.Char()
    website = fields.Char()
    screen_thumb = fields.Char()
    print_thumb = fields.Char()
    notify_reply_to_email = fields.Integer()
    domain = fields.Char()
    return_portal_url = fields.Char(compute="_compute_return_portal_url")
    notify_bcc_email = fields.Integer()
    hide_powered_by = fields.Boolean()
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    def _compute_return_portal_url(self):
        for brand in self:
            url = f"https://{brand.domain}.shipping-portal.com/rp/"
            brand.return_portal_url = url

    def action_create_return_parcel(self):
        self.ensure_one()
        action_name = (
            "delivery_sendcloud_oca.action_sendcloud_create_return_parcel_wizard"
        )
        [action] = self.env.ref(action_name).read()
        action["context"] = "{'default_brand_id': %s}" % (self.id)
        return action

    @api.model
    def _prepare_sendcloud_brands_from_response(self, records_data):
        return {
            "sendcloud_code": records_data.get("id"),
            "name": records_data.get("name"),
            "color": records_data.get("color"),
            "secondary_color": records_data.get("secondary_color"),
            "website": records_data.get("website"),
            "screen_thumb": records_data.get("screen_thumb"),
            "print_thumb": records_data.get("print_thumb"),
            "notify_reply_to_email": records_data.get("notify_reply_to_email"),
            "domain": records_data.get("domain"),
            "notify_bcc_email": records_data.get("notify_bcc_email"),
            "hide_powered_by": records_data.get("hide_powered_by"),
        }

    @api.model
    def sendcloud_update_brands(self, brand_data, company):
        # All records
        all_records = company.sendcloud_brand_ids

        # Existing records
        existing_records = all_records.filtered(
            lambda c: c.sendcloud_code in [record.get("id") for record in brand_data]
        )

        # Existing records map (internal code -> existing record)
        existing_records_map = {}
        for existing in existing_records:
            if existing.sendcloud_code not in existing_records_map:
                existing_records_map[existing.sendcloud_code] = self.env[
                    "sendcloud.brand"
                ]
            existing_records_map[existing.sendcloud_code] |= existing

        # Disabled records
        disabled_records = all_records - existing_records
        disabled_records.write({"active": False})

        # Created records
        vals_list = []
        for record in brand_data:
            vals = self._prepare_sendcloud_brands_from_response(record)
            if record.get("id") in existing_records_map:
                existing_records_map[record.get("id")].write(vals)
            else:
                vals["company_id"] = company.id
                vals_list += [vals]
        new_created_records = self.create(vals_list)

        # Updated records
        updated_records = existing_records + new_created_records
        updated_records.write({"active": True})

    @api.model
    def sendcloud_sync_brands(self):
        for company in self.env["res.company"].search([]):
            integration = company.sendcloud_default_integration_id
            if integration:
                brands_data = integration.get_brands()
                self.sendcloud_update_brands(brands_data, company)
