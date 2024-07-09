# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sendcloud_integration_ids = fields.One2many(
        "sendcloud.integration", "company_id", string="Sendcloud Integrations"
    )
    sendcloud_brand_ids = fields.One2many(
        "sendcloud.brand", "company_id", string="Sendcloud Brands"
    )
    sendcloud_return_ids = fields.One2many(
        "sendcloud.return", "company_id", string="Sendcloud Returns"
    )
    sendcloud_invoice_ids = fields.One2many(
        "sendcloud.invoice", "company_id", string="Sendcloud Invoices"
    )
    sendcloud_sender_address_ids = fields.One2many(
        "sendcloud.sender.address", "company_id", string="Sendcloud Sender Addresses"
    )

    sendcloud_default_integration_id = fields.Many2one(
        "sendcloud.integration", compute="_compute_sendcloud_default_integration_id"
    )

    is_sendcloud_test_mode = fields.Boolean()
    sendcloud_auto_create_invoice = fields.Boolean()

    @api.depends(
        "sendcloud_integration_ids.public_key",
        "sendcloud_integration_ids.secret_key",
        "sendcloud_integration_ids.sequence",
    )
    def _compute_sendcloud_default_integration_id(self):
        for company in self:
            integrations = company.sendcloud_integration_ids
            integrations = integrations.filtered(
                lambda i: i.public_key and i.secret_key
            ).sorted(key=lambda i: i.sequence)
            company.sendcloud_default_integration_id = fields.first(integrations)
