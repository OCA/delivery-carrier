# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

# Whether you want to pull all the existing integrations from Sendcloud.
SENDCLOUD_GET_ALL_EXISTING_INTEGRATIONS = False


class SendcloudIntegration(models.Model):
    _name = "sendcloud.integration"
    _description = "Sendcloud Integrations"
    _inherit = "sendcloud.request"
    _rec_name = "shop_name"
    _order = "sequence, id"
    _log_access = False

    shop_name = fields.Char(required=True)
    sequence = fields.Integer(help="Determine the display order", default=10)
    public_key = fields.Char(readonly=False)
    secret_key = fields.Char(readonly=False)
    sendcloud_code = fields.Integer(readonly=True)
    shop_url = fields.Char()
    service_point_enabled = fields.Boolean()
    service_point_carriers = fields.Text(default="[]")
    service_point_carrier_ids = fields.Many2many(
        "sendcloud.carrier",
        string="Carriers",
        compute="_compute_service_point_carrier_ids",
        inverse="_inverse_service_point_carrier_ids",
    )
    webhook_active = fields.Boolean()
    webhook_url = fields.Char()
    database = fields.Char()  # TODO alert in case db is copied
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.onchange("company_id")
    def _onchange_company_id(self):
        base_url = self.env["sendcloud.request"]._param_web_base_url()
        company_id = self.company_id.id
        path = self._default_integration_webhook(company_id)
        self.webhook_url = base_url + path

    @api.depends("service_point_carriers")
    def _compute_service_point_carrier_ids(self):
        for integration in self:
            carriers_list = safe_eval(integration.service_point_carriers)
            domain = [("sendcloud_code", "in", carriers_list)]
            sendcloud_carriers = self.env["sendcloud.carrier"].search(domain)
            integration.service_point_carrier_ids = sendcloud_carriers

    def _inverse_service_point_carrier_ids(self):
        for integration in self:
            carriers = integration.service_point_carrier_ids
            carriers_list = carriers.mapped("sendcloud_code")
            integration.service_point_carriers = str(carriers_list)

    @api.model
    def _prepare_sendcloud_integration_from_response(self, integration):
        return {
            "shop_name": integration.get("shop_name"),
            "sendcloud_code": integration.get("id"),
            "shop_url": integration.get("shop_url"),
            "service_point_enabled": integration.get("service_point_enabled"),
            "service_point_carriers": integration.get("service_point_carriers"),
            "webhook_active": integration.get("webhook_active"),
            "webhook_url": integration.get("webhook_url"),
        }

    @api.model
    def sendcloud_create_update_integrations(self, req_integrations, company):
        # Error in fetching integrations if its not a list
        if not isinstance(req_integrations, list):
            return
        # All integrations
        domain = [("company_id", "=", company.id)]
        all_integrations = (
            self.env["sendcloud.integration"]
            .with_context(active_test=False)
            .search(domain)
        )
        # Existing records
        integrations_list = [integration.get("id") for integration in req_integrations]
        existing_integrations = all_integrations.filtered(
            lambda c: c.sendcloud_code and c.sendcloud_code in integrations_list
        )

        # Existing integrations map (internal code -> existing integration)
        existing_integrations_map = {}
        for existing in existing_integrations:
            if (
                existing.sendcloud_code
                and existing.sendcloud_code not in existing_integrations_map
            ):
                existing_integrations_map[existing.sendcloud_code] = self.env[
                    "sendcloud.integration"
                ]
            existing_integrations_map[existing.sendcloud_code] |= existing

        # Empty integrations
        empty_integrations = all_integrations.filtered(lambda c: not c.sendcloud_code)

        # Disabled integrations
        disabled_integrations = (
            all_integrations - existing_integrations - empty_integrations
        )
        disabled_integrations.write({"active": False})

        # Created integrations
        vals_list = []
        for integration in req_integrations:
            vals = self._prepare_sendcloud_integration_from_response(integration)
            vals["company_id"] = company.id
            if integration.get("id") in existing_integrations_map:
                existing_integrations_map[integration.get("id")].write(vals)
            elif empty_integrations:
                empty_integrations.write(vals)

        new_created_integrations = self.env["sendcloud.integration"]
        if vals_list and SENDCLOUD_GET_ALL_EXISTING_INTEGRATIONS:
            new_created_integrations = self.env["sendcloud.integration"].create(
                vals_list
            )

        # Updated integrations
        updated_integrations = existing_integrations + new_created_integrations
        updated_integrations.write({"active": True})

        # Carriers
        self.sendcloud_update_carriers(updated_integrations)

    @api.model
    def sendcloud_update_carriers(self, updated_integrations):
        retrieved_carriers = []
        for integration in updated_integrations:
            retrieved_carriers += safe_eval(integration.service_point_carriers)
        self.env["sendcloud.carrier"]._create_update_carriers(retrieved_carriers)

    def action_sendcloud_update_integrations(self):
        self.ensure_one()
        integration = self.company_id.sendcloud_default_integration_id
        req_integrations = integration.get_integrations()
        self.sendcloud_create_update_integrations(req_integrations, self.company_id)

    def _update_in_sendcloud(self, vals):
        self.ensure_one()
        code = self.sendcloud_code
        to_update_vals = {}
        for name in self._sendcloud_updatable_fields():
            if name in vals:
                to_update_vals.update({name: vals.get(name)})

        integration = self.company_id.sendcloud_default_integration_id
        response = integration.update_integration(code, to_update_vals)
        if isinstance(response, dict):  # TODO
            for name in self._sendcloud_updatable_fields():
                if name in response:
                    vals[name] = response[name]
        return vals

    @api.model
    def _sendcloud_updatable_fields(self):
        return [
            "webhook_active",
            "webhook_url",
            "shop_url",
            "shop_name",
            "service_point_enabled",
            "service_point_carriers",
        ]

    def write(self, vals):
        if self.env.context.get("skip_update_in_sendcloud"):
            return super().write(vals)

        if any(item not in self._sendcloud_updatable_fields() for item in vals):
            return super().write(vals)

        for record in self:
            formatted_vals = record._prepare_sendcloud_integration_from_record(vals)
            updated_vals = record._update_in_sendcloud(formatted_vals)
            super(SendcloudIntegration, record).write(updated_vals)
        return self

    def _prepare_sendcloud_integration_from_record(self, vals):
        self.ensure_one()
        formatted_vals = vals
        if "service_point_enabled" in vals and "service_point_carriers" not in vals:
            vals["service_point_carriers"] = self.service_point_carriers
        if "service_point_carriers" in vals and "service_point_enabled" not in vals:
            vals["service_point_enabled"] = self.service_point_enabled
        if vals.get("service_point_enabled") and not safe_eval(
            vals.get("service_point_carriers")
        ):
            raise UserError(_("Sendcloud: select at least one service point carrier"))
        if "service_point_carriers" in vals and isinstance(
            vals["service_point_carriers"], str
        ):
            formatted_vals["service_point_carriers"] = safe_eval(
                vals["service_point_carriers"]
            )
        return formatted_vals
