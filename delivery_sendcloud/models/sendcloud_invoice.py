# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from datetime import datetime

from odoo import api, fields, models


class SendcloudInvoice(models.Model):
    _name = "sendcloud.invoice"
    _description = "Sendcloud Invoice"
    _rec_name = "sendcloud_code"

    @api.model
    def _selection_invoice_type(self):
        return [
            ("periodic", "Periodical"),
            ("forced", "Created manually"),
            ("initial_payment", "Initial payment"),
            ("other", "Other"),
        ]

    sendcloud_code = fields.Integer(required=True)
    invoice_date = fields.Datetime()
    is_paid = fields.Boolean()
    item_ids = fields.One2many("sendcloud.invoice.item", "sendcloud_invoice_id")
    price_excl = fields.Float()
    price_incl = fields.Float()
    ref = fields.Char()
    invoice_type = fields.Selection(
        selection=lambda self: self._selection_invoice_type(), readonly=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.model
    def _prepare_sendcloud_invoice_from_response(self, records_data):
        invoice_date = records_data.get("date")
        invoice_date = datetime.strptime(invoice_date, "%d-%m-%Y %H:%M:%S")

        vals = {
            "sendcloud_code": records_data.get("id"),
            "invoice_date": invoice_date,
            "is_paid": records_data.get("isPayed"),
            "price_excl": records_data.get("price_excl"),
            "price_incl": records_data.get("price_incl"),
            "ref": records_data.get("ref"),
            "invoice_type": records_data.get("type"),
        }
        if isinstance(records_data.get("items"), list):
            item_ids = [(5, False, False)]
            item_ids += [
                (0, False, {"sendcloud_code": values["id"], "name": values["name"]})
                for values in records_data.get("items")
            ]
            vals.update({"item_ids": item_ids})
        return vals

    @api.model
    def sendcloud_update_invoices(self, invoice_data, company):
        # All records
        all_records = company.sendcloud_invoice_ids

        # Existing records
        existing_records = all_records.filtered(
            lambda c: c.sendcloud_code in [record.get("id") for record in invoice_data]
        )

        # Existing records map (internal code -> existing record)
        existing_records_map = {}
        for existing in existing_records:
            if existing.sendcloud_code not in existing_records_map:
                existing_records_map[existing.sendcloud_code] = self.env[
                    "sendcloud.invoice"
                ]
            existing_records_map[existing.sendcloud_code] |= existing

        # Disabled records
        disabled_records = all_records - existing_records
        disabled_records.write({"active": False})

        # Created records
        vals_list = []
        for record in invoice_data:
            vals = self._prepare_sendcloud_invoice_from_response(record)
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
    def sendcloud_sync_invoices(self):
        for company in self.env["res.company"].search([]):
            integration = company.sendcloud_default_integration_id
            if integration:
                invoice_data = integration.get_user_invoices()
                self.sendcloud_update_invoices(invoice_data, company)

    def sendcloud_update_invoice_details(self, invoice_data):
        self.ensure_one()
        self.write(self._prepare_sendcloud_invoice_from_response(invoice_data))

    def button_get_invoice_details(self):
        self.ensure_one()
        integration = self.company_id.sendcloud_default_integration_id
        if integration:
            self.item_ids.unlink()
            invoice_data = integration.get_user_invoice(self.sendcloud_code)
            self.sendcloud_update_invoice_details(invoice_data)
