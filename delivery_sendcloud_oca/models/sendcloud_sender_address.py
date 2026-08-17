# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, fields, models


class SendcloudSenderAddress(models.Model):
    _name = "sendcloud.sender.address"
    _description = "Sendcloud Sender Address"
    _rec_name = "company_name"

    sendcloud_code = fields.Integer(required=True)
    company_name = fields.Char()
    contact_name = fields.Char()
    email = fields.Char()
    telephone = fields.Char()
    street = fields.Char()
    house_number = fields.Char()
    postal_box = fields.Char()
    postal_code = fields.Char()
    city = fields.Char()
    country = fields.Char()
    vat_number = fields.Char()
    eori_number = fields.Char()
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)

    @api.model
    def _prepare_sendcloud_addresses_from_response(self, addresses_data):
        return {
            "sendcloud_code": addresses_data.get("id"),
            "company_name": addresses_data.get("company_name"),
            "contact_name": addresses_data.get("contact_name"),
            "email": addresses_data.get("email"),
            "telephone": addresses_data.get("telephone"),
            "street": addresses_data.get("street"),
            "house_number": addresses_data.get("house_number"),
            "postal_box": addresses_data.get("postal_box"),
            "postal_code": addresses_data.get("postal_code"),
            "city": addresses_data.get("city"),
            "country": addresses_data.get("country"),
            "vat_number": addresses_data.get("vat_number"),
            "eori_number": addresses_data.get("eori_number"),
        }

    @api.model
    def sendcloud_update_sender_address(self, sender_addresses, company):
        # All addresses
        domain = [("company_id", "=", company.id)]
        all_records = self.with_context(active_test=False).search(domain)

        # Existing records
        addresses_list = [address.get("id") for address in sender_addresses]
        existing_records = all_records.filtered(
            lambda c: c.sendcloud_code in addresses_list
        )

        # Existing addresses map (internal code -> existing address)
        existing_addresses_map = {}
        for existing in existing_records:
            if existing.sendcloud_code not in existing_addresses_map:
                existing_addresses_map[existing.sendcloud_code] = self.env[
                    "sendcloud.sender.address"
                ]
            existing_addresses_map[existing.sendcloud_code] |= existing

        # Disabled addresses
        disabled_records = all_records - existing_records
        disabled_records.write({"active": False})

        # Created addresses
        vals_list = []
        for address in sender_addresses:
            vals = self._prepare_sendcloud_addresses_from_response(address)
            if address.get("id") in existing_addresses_map.keys():
                existing_addresses_map[address.get("id")].write(vals)
            else:
                vals["company_id"] = company.id
                vals_list += [vals]
        new_created_records = self.create(vals_list)

        # Updated addresses
        updated_records = existing_records + new_created_records
        updated_records.write({"active": True})

    @api.model
    def sendcloud_sync_sender_address(self):
        for company in self.env["res.company"].search([]):
            integration = company.sendcloud_default_integration_id
            if integration:
                sender_addresses = integration.get_sender_address()
                self.sendcloud_update_sender_address(sender_addresses, company)
