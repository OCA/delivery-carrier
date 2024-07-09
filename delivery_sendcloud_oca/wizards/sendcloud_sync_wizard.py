# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import _, fields, models
from odoo.exceptions import UserError


class SendcloudSyncWizard(models.TransientModel):
    _name = "sendcloud.sync.wizard"
    _description = "Sendcloud Sync Wizard"

    brands = fields.Boolean(default=True)
    returns = fields.Boolean(default=True)
    parcel_statuses = fields.Boolean(default=True)
    parcels = fields.Boolean(default=True)
    invoices = fields.Boolean(default=True)
    sender_addresses = fields.Boolean(default=True)
    shipping_methods = fields.Boolean(default=True)

    def button_sync(self):
        company = self.env.company
        integration = company.sendcloud_default_integration_id
        if not integration:
            raise UserError(
                _("No Sendcloud integrations found. Setup an integration first.")
            )

        if self.brands:
            self.env["sendcloud.brand"].sendcloud_sync_brands()
        if self.returns:
            self.env["sendcloud.return"].sendcloud_sync_returns()
        if self.parcel_statuses:
            self.env["sendcloud.parcel.status"].sendcloud_sync_parcel_statuses()
        if self.parcels:
            self.env["sendcloud.parcel"].sendcloud_sync_parcels()
        if self.invoices:
            self.env["sendcloud.invoice"].sendcloud_sync_invoices()
        if self.sender_addresses:
            self.env["sendcloud.sender.address"].sendcloud_sync_sender_address()
        if self.shipping_methods:
            self.env["delivery.carrier"].sendcloud_sync_shipping_method()
        self.env["onboarding.onboarding.step"].action_validate_step(
            "delivery_sendcloud_oca.onboarding_sync_step"
        )
