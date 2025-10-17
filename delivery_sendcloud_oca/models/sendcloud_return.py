# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, fields, models


class SendcloudReturn(models.Model):
    _name = "sendcloud.return"
    _description = "Sendcloud Return"
    _rec_name = "sendcloud_code"

    return_response_cache = fields.Text(default="{}")
    sendcloud_code = fields.Integer(required=True)
    email = fields.Char()
    created_at = fields.Char()  # TODO
    reason = fields.Integer()
    outgoing_parcel_code = fields.Integer()
    incoming_parcel_code = fields.Integer()
    outgoing_parcel_id = fields.Many2one(
        "sendcloud.parcel", compute="_compute_parcel_id"
    )
    incoming_parcel_id = fields.Many2one(
        "sendcloud.parcel", compute="_compute_parcel_id"
    )
    message = fields.Text()
    status = fields.Char()
    refund_type = fields.Char()
    total_refund = fields.Float()
    refunded_at = fields.Char()
    refund_message = fields.Char()
    status_display = fields.Char()
    is_cancellable = fields.Boolean()
    label_cost = fields.Float()
    items_cost = fields.Float()
    delivered_at = fields.Char()
    delivery_option = fields.Selection(
        [
            ("drop_off_point", "Drop Off Point"),
            ("in_store", "In Store"),
            ("drop_off_labelless", "Labelless Drop Off"),
        ]
    )

    outgoing_parcel_tracking_url = fields.Char()
    outgoing_parcel_tracking_number = fields.Char()
    outgoing_parcel_parcel_status = fields.Char()
    outgoing_parcel_global_status_slug = fields.Char()
    outgoing_parcel_brand_name = fields.Char()
    outgoing_parcel_order_number = fields.Char()
    outgoing_parcel_from_email = fields.Char()
    outgoing_parcel_deleted = fields.Boolean()

    incoming_parcel_tracking_url = fields.Char()
    incoming_parcel_tracking_number = fields.Char()
    incoming_parcel_parcel_status = fields.Char()
    incoming_parcel_global_status_slug = fields.Char()
    incoming_parcel_brand_name = fields.Char()
    incoming_parcel_order_number = fields.Char()
    incoming_parcel_from_email = fields.Char()
    incoming_parcel_deleted = fields.Boolean()

    incoming_parcel_status_code = fields.Integer()
    incoming_parcel_status_message = fields.Char()
    incoming_parcel_status_global_status_slug = fields.Char()

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.depends("outgoing_parcel_code", "incoming_parcel_code")
    def _compute_parcel_id(self):
        for record in self:
            record.outgoing_parcel_id = self.env["sendcloud.parcel"].search(
                [("sendcloud_code", "=", record.outgoing_parcel_code)], limit=1
            )
            record.incoming_parcel_id = self.env["sendcloud.parcel"].search(
                [("sendcloud_code", "=", record.incoming_parcel_code)], limit=1
            )

    @api.model
    def _prepare_sendcloud_return_from_response(self, record_data):
        res = {
            "sendcloud_code": record_data.get("id"),
            "return_response_cache": record_data,
            "email": record_data.get("email"),
            "created_at": record_data.get("created_at"),
            "outgoing_parcel_code": record_data.get("outgoing_parcel"),
            "incoming_parcel_code": record_data.get("incoming_parcel"),
            "reason": record_data.get("reason"),
            "message": record_data.get("message"),
            "status": record_data.get("status"),
            "status_display": record_data.get("status_display"),
            "is_cancellable": record_data.get("is_cancellable"),
            "label_cost": record_data.get("label_cost"),
            "items_cost": record_data.get("items_cost"),
            "delivered_at": record_data.get("delivered_at"),
            "delivery_option": record_data.get("delivery_option"),
            "outgoing_parcel_tracking_url": record_data.get(
                "outgoing_parcel_data", {}
            ).get("tracking_url"),
            "outgoing_parcel_tracking_number": record_data.get(
                "outgoing_parcel_data", {}
            ).get("tracking_number"),
            "outgoing_parcel_parcel_status": record_data.get(
                "outgoing_parcel_data", {}
            ).get("parcel_status"),
            "outgoing_parcel_global_status_slug": record_data.get(
                "outgoing_parcel_data", {}
            ).get("global_status_slug"),
            "outgoing_parcel_brand_name": record_data.get(
                "outgoing_parcel_data", {}
            ).get("brand_name"),
            "outgoing_parcel_order_number": record_data.get(
                "outgoing_parcel_data", {}
            ).get("order_number"),
            "outgoing_parcel_from_email": record_data.get(
                "outgoing_parcel_data", {}
            ).get("from_email"),
            "outgoing_parcel_deleted": record_data.get("outgoing_parcel_data", {}).get(
                "deleted"
            ),
            "incoming_parcel_tracking_url": record_data.get(
                "incoming_parcel_data", {}
            ).get("tracking_url"),
            "incoming_parcel_tracking_number": record_data.get(
                "incoming_parcel_data", {}
            ).get("tracking_number"),
            "incoming_parcel_parcel_status": record_data.get(
                "incoming_parcel_data", {}
            ).get("parcel_status"),
            "incoming_parcel_global_status_slug": record_data.get(
                "incoming_parcel_data", {}
            ).get("global_status_slug"),
            "incoming_parcel_brand_name": record_data.get(
                "incoming_parcel_data", {}
            ).get("brand_name"),
            "incoming_parcel_order_number": record_data.get(
                "incoming_parcel_data", {}
            ).get("order_number"),
            "incoming_parcel_from_email": record_data.get(
                "incoming_parcel_data", {}
            ).get("from_email"),
            "incoming_parcel_deleted": record_data.get("incoming_parcel_data", {}).get(
                "deleted"
            ),
            "incoming_parcel_status_code": record_data.get(
                "incoming_parcel_status", {}
            ).get("id"),
            "incoming_parcel_status_message": record_data.get(
                "incoming_parcel_status", {}
            ).get("message"),
            "incoming_parcel_status_global_status_slug": record_data.get(
                "incoming_parcel_status", {}
            ).get("global_status_slug"),
        }

        refund = record_data.get("refund")
        if refund:
            res.update(
                {
                    "refund_type": refund["refund_type"]["code"],
                    "total_refund": refund["total_refund"],
                    "refunded_at": refund["refunded_at"],
                    "refund_message": refund["message"],
                }
            )

        return res

    @api.model
    def sendcloud_create_or_update_returns(self, return_data, company):
        if isinstance(return_data, dict):
            return_data = [return_data]

        # All records
        all_records = company.sendcloud_return_ids

        # Existing records
        existing_records = all_records.filtered(
            lambda c: c.sendcloud_code in [record.get("id") for record in return_data]
        )

        # Existing records map (internal code -> existing record)
        existing_records_map = {}
        for existing in existing_records:
            if existing.sendcloud_code not in existing_records_map:
                existing_records_map[existing.sendcloud_code] = self.env[
                    "sendcloud.return"
                ]
            existing_records_map[existing.sendcloud_code] |= existing

        # Disabled records
        disabled_records = all_records - existing_records
        disabled_records.write({"active": False})

        # Created records
        vals_list = []
        for record in return_data:
            vals = self._prepare_sendcloud_return_from_response(record)
            if record.get("id") in existing_records_map:
                existing_records_map[record.get("id")].write(vals)
            else:
                vals["company_id"] = company.id
                vals_list += [vals]
        new_created_records = self.create(vals_list)

        # Updated records
        updated_records = existing_records + new_created_records
        updated_records.write({"active": True})
        return updated_records

    @api.model
    def sendcloud_sync_returns(self):
        for company in self.env["res.company"].search([]):
            integration = company.sendcloud_default_integration_id
            if integration:
                return_data = integration.get_returns()  # TODO paging
                self.sendcloud_create_or_update_returns(return_data, company)
