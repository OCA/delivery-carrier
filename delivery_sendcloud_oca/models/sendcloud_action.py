# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import json
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SendcloudAction(models.Model):
    _name = "sendcloud.action"
    _description = "Sendcloud Action"
    _rec_name = "action"
    _order = "id desc"

    company_id = fields.Many2one("res.company", required=True)
    sendcloud_integration_id = fields.Many2one(
        "sendcloud.integration"
    )  # Could be empty, eg.: in case of public get

    exitcode = fields.Char()
    action = fields.Char()
    timestamp = fields.Char()
    message_type = fields.Selection(
        [("sent", "Sent"), ("received", "Received")], required=True
    )
    model = fields.Char()
    resid = fields.Integer()
    record_id = fields.Reference(
        selection="_reference_models", compute="_compute_resource_record", readonly=True
    )

    sent_payload = fields.Text()
    message = fields.Text(string="Received Message")
    response_time = fields.Float(string="Response Time (sec)")

    is_processed = fields.Boolean()
    date_last_success = fields.Datetime()

    error_message = fields.Char()
    error_on_parsing = fields.Boolean()

    @api.model
    def _reference_models(self):
        models = self.env["ir.model"].sudo().search([])
        return [(model.model, model.name) for model in models]

    @api.depends("model", "resid")
    def _compute_resource_record(self):
        for action in self:
            if action.model and action.resid:
                action.record_id = f"{action.model},{action.resid}"
            else:
                action.record_id = False

    # flake8: noqa: C901
    def parse_result(self):
        self.ensure_one()

        _logger.info("Sendcloud parsing message:%s", self.message)

        try:
            message = json.loads(self.message)
        except Exception as e:
            self.error_on_parsing = True
            self.error_message = str(e)
            return False
        integration = self.sendcloud_integration_id
        if message.get("action") == "integration_updated":
            integration_data = message.get("integration")
            if integration_data:
                vals = self.env[
                    "sendcloud.integration"
                ]._prepare_sendcloud_integration_from_response(integration_data)
                if integration:
                    integration.with_context(skip_update_in_sendcloud=True).write(vals)
                else:
                    vals["company_id"] = self.company_id.id
                    integration = self.env["sendcloud.integration"].create(vals)
                self._update_action_log(integration)
        elif message.get("action") == "integration_connected":
            integration_data = message.get("integration")
            if integration_data:
                code = integration_data["id"]
                existing_integration = (
                    self.env["sendcloud.integration"]
                    .with_context(active_test=False)
                    .search(
                        [
                            ("sendcloud_code", "=", code),
                            ("company_id", "=", self.company_id.id),
                        ],
                        limit=1,
                    )
                )
                if existing_integration:
                    integration = existing_integration
                else:
                    vals = self.env[
                        "sendcloud.integration"
                    ]._prepare_sendcloud_integration_from_response(integration_data)
                    vals["company_id"] = self.company_id.id
                    integration = self.env["sendcloud.integration"].create(vals)
                self._update_action_log(integration)
        elif message.get("action") == "integration_deleted":
            integration.write({"active": False})
            self._update_action_log(integration)
        elif message.get("action") == "integration_credentials":
            _logger.info("Sendcloud integration_credentials")
            if integration:
                _logger.info(
                    "Sendcloud integration_credentials integration_id:%s",
                    integration.id,
                )
                integration.write(
                    {
                        "public_key": message["public_key"],
                        "secret_key": message["secret_key"],
                        "sendcloud_code": message["integration_id"],
                    }
                )
                integration.with_context(
                    skip_raise_error_401=True, skip_sendcloud_check_response=True
                ).action_sendcloud_update_integrations()
                self._update_action_log(integration)
                self.env["onboarding.onboarding.step"].action_validate_step(
                    "delivery_sendcloud_oca.onboarding_integration_step"
                )
        elif message.get("action") == "parcel_status_changed":
            parcel_data = message.get("parcel")
            picking = self.env["stock.picking"]
            if parcel_data.get("shipment_uuid"):
                picking = self.env["stock.picking"].search(
                    [
                        ("sendcloud_shipment_uuid", "=", parcel_data["shipment_uuid"]),
                    ],
                    limit=1,
                )
            if not picking:
                sendcloud_order_code = parcel_data.get("external_order_id")
                sendcloud_shipment_code = parcel_data.get("external_shipment_id")
                if sendcloud_shipment_code.isdigit() and sendcloud_order_code.isdigit():
                    picking = self.env["stock.picking"].search(
                        [
                            ("id", "=", int(sendcloud_shipment_code)),
                            ("sale_id", "=", int(sendcloud_order_code)),
                        ]
                    )
                elif sendcloud_shipment_code and sendcloud_order_code:
                    picking = self.env["stock.picking"].search(
                        [
                            ("sendcloud_shipment_code", "=", sendcloud_shipment_code),
                            ("sale_id.sendcloud_order_code", "=", sendcloud_order_code),
                        ],
                        limit=1,
                    )
            if not picking:
                sendcloud_code = parcel_data["id"]
                picking = (
                    self.env["sendcloud.parcel"]
                    .search([("sendcloud_code", "=", sendcloud_code)])
                    .mapped("picking_id")
                )
            if picking and picking.sendcloud_parcel_ids:
                parcels = picking._sendcloud_create_update_received_parcels(
                    [parcel_data], self.company_id.id
                )
                parcel = parcels.filtered(
                    lambda p: p.sendcloud_code == parcel_data["id"]
                )
                self._update_action_log(parcel)

    def _update_action_log(self, record):
        self.ensure_one()
        self.write(
            {
                "model": record._name,
                "resid": record.id,
                "error_on_parsing": False,
                "error_message": "",
                "date_last_success": fields.Datetime.now(),
            }
        )

    def reparse_message(self):
        self.ensure_one()
        self.parse_result()
        self.is_processed = True

    @api.model
    def sendcloud_delete_old_actions(self, days=7):
        date = fields.Datetime.to_string(fields.Date.today() - relativedelta(days=days))
        self.search([("create_date", "<", date)]).unlink()
