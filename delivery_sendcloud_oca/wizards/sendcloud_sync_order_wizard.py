# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class SendcloudSyncOrderWizard(models.TransientModel):
    _name = "sendcloud.sync.order.wizard"
    _description = "Sendcloud Sync Order Wizard"

    sync_from_date = fields.Date(
        default=lambda self: fields.Date.context_today(self) + relativedelta(days=-30),
        required=True,
    )

    def button_sync(self):
        company = self.env.company
        integration = company.sendcloud_default_integration_id
        if not integration:
            raise UserError(
                _("No Sendcloud integrations found. Setup an integration first.")
            )

        pickings = self.env["stock.picking"].search(
            [
                ("delivery_type", "=", "sendcloud"),
                ("picking_type_code", "=", "outgoing"),
                ("sale_id", "!=", False),
                ("date", ">=", self.sync_from_date),
            ]
        )
        if not pickings:
            raise UserError(
                _("There are no outgoing shipments set with Sendcloud shipping method.")
            )
        pickings._sync_picking_to_sendcloud()
