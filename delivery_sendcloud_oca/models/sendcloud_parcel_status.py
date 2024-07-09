# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, fields, models


class SendcloudParcelStatus(models.Model):
    _name = "sendcloud.parcel.status"
    _description = "Sendcloud Parcel Statuses"
    _rec_name = "message"

    message = fields.Char(required=True)
    sendcloud_code = fields.Char(required=True)

    @api.model
    def _prepare_sendcloud_parcel_statuses_from_response(self, records_data):
        return {
            "sendcloud_code": str(records_data.get("id")),
            "message": records_data.get("message"),
        }

    @api.model
    def sendcloud_update_parcel_statuses(self, integration):
        records_data = integration.get_parcels_statuses()

        # All records
        all_records = self.search([])

        # Existing records
        existing_records = all_records.filtered(
            lambda c: c.sendcloud_code in [str(record["id"]) for record in records_data]
        )

        # Existing records map (internal code -> existing record)
        existing_records_map = {}
        for existing in existing_records:
            if existing.sendcloud_code not in existing_records_map:
                existing_records_map[existing.sendcloud_code] = self.env[
                    "sendcloud.parcel.status"
                ]
            existing_records_map[existing.sendcloud_code] |= existing

        # Created records
        vals_list = []
        for record in records_data:
            vals = self._prepare_sendcloud_parcel_statuses_from_response(record)
            if str(record["id"]) in existing_records_map:
                existing_records_map[str(record["id"])].write(vals)
            else:
                vals_list += [vals]
        self.create(vals_list)

    @api.model
    def sendcloud_sync_parcel_statuses(self):
        for company in self.env["res.company"].search([]):
            integration = company.sendcloud_default_integration_id
            if integration:
                self.sendcloud_update_parcel_statuses(integration)
