# Copyright 2021 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

from urllib.parse import urlencode

import requests

from odoo import _, api, fields, models


class SendcloudIntegrationWizard(models.TransientModel):
    _name = "sendcloud.integration.wizard"
    _description = "Sendcloud Integration Wizard"

    base_url = fields.Char(compute="_compute_base_url")
    integration_request_url = fields.Char(compute="_compute_integration_request_url")
    error_message = fields.Text(readonly=True)
    info_message = fields.Text(readonly=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    is_sendcloud_test_mode = fields.Boolean(compute="_compute_is_sendcloud_test_mode")

    @api.depends("company_id.is_sendcloud_test_mode")
    def _compute_is_sendcloud_test_mode(self):
        for record in self:
            record.is_sendcloud_test_mode = record.company_id.is_sendcloud_test_mode

    def _compute_base_url(self):
        for wizard in self:
            wizard.base_url = self.env["sendcloud.request"]._param_web_base_url()

    def _get_odoo_connect_url(self):
        return "https://panel.sendcloud.sc/shops/odoo/connect/"

    def _compute_integration_request_url(self):
        for wizard in self:
            request_url = self._get_odoo_connect_url()
            Request = self.env["sendcloud.request"]
            webhook = Request._default_integration_webhook(self.env.company.id)
            querystring = urlencode(
                {
                    "url_webshop": wizard.base_url,
                    "webhook_url": wizard.base_url + webhook,
                    "shop_name": self.env.cr.dbname + " " + str(self.env.company.id),
                }
            )
            wizard.integration_request_url = f"{request_url}?{querystring}".format(
                request_url=request_url, querystring=querystring
            )

    def check_webhook_url(self):
        self.ensure_one()
        default_webhook = self.env["sendcloud.request"]._default_integration_webhook(
            self.env.company.id
        )
        url = self.base_url + default_webhook
        try:
            resp = requests.post(url=url, json={}, timeout=10)
        except Exception as err:
            self.error_message = _("Error while checking the webhook connection.\n")
            self.error_message += "%s\n" % str(err)
            self.error_message += _("Webhook URL: %(url)s\n") % {"url": url}
            return False
        if resp.status_code != 200:
            err_msg = _("Webhook URL: %(reason)s (error code %(status_code)s)") % (
                {"reason": resp.reason, "status_code": resp.status_code}
            )
            self.error_message = _("Error while checking the webhook connection.\n")
            self.error_message += "%s\n" % err_msg
            self.error_message += "URL: %s\n" % url
            return False
        return True

    def button_update(self):
        self = self.sudo()
        integrations = self.env.company.sendcloud_integration_ids
        integrations = integrations.filtered(
            lambda i: not i.sendcloud_code and not i.public_key and not i.secret_key
        )
        if not integrations:
            vals = {
                "shop_name": "API Integration " + self.env.company.name,
                "company_id": self.env.company.id,
            }
            self.env["sendcloud.integration"].create(vals)
        if not self.check_webhook_url():
            action_name = (
                "delivery_sendcloud_oca.action_sendcloud_onboarding_integration_wizard"
            )
            action = self.env.ref(action_name).read()[0]
            action["res_id"] = self.id
            return action
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.integration_request_url,
        }
