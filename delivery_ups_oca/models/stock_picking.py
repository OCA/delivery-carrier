# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ups_document_identifier = fields.Char(
        "DocumentID", help="Forms History Document ID", readonly=True, copy=False
    )
    ups_paperless_document_ids = fields.One2many(
        "ups.paperless.document", "ups_stock_picking_id", string="Paperless Document"
    )
    ups_paperless_auto_send = fields.Boolean(
        string="Automatically Send",
        help="True if you need to send a UPS Paperless Invoice",
    )

    def ups_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "ups" or not tracking_ref:
            return
        return self.carrier_id.ups_get_label(tracking_ref)

    def generate_paperless_invoice(self):
        return self.carrier_id.send_ups_paperless_invoice(self)

    def _get_ups_paperless_auto_send(self):
        self.ensure_one()
        return bool(
            self.carrier_id.delivery_type == "ups"
            and self.partner_id
            and self.partner_id.country_id
            in self.carrier_id.ups_paperless_country_group_ids.mapped("country_ids")
        )

    @api.onchange("carrier_id", "partner_id")
    def _onchange_ups_paperless_auto_send(self):
        for rec in self:
            rec.ups_paperless_auto_send = rec._get_ups_paperless_auto_send()

    @api.model_create_multi
    def create(self, vals_list):
        """Override to set ups_paperless_auto_send based on country group"""
        pickings = super().create(vals_list)
        for picking in pickings:
            if picking._get_ups_paperless_auto_send():
                picking.ups_paperless_auto_send = True
        return pickings

    def button_validate(self):
        """Override to trigger paperless invoice upload when validating a picking"""
        res = super().button_validate()
        for picking in self:
            if (
                picking.carrier_id
                and picking.carrier_id.delivery_type == "ups"
                and picking.ups_paperless_auto_send
                and not picking.ups_document_identifier
                and picking.ups_paperless_document_ids
            ):
                try:
                    picking.carrier_id.send_ups_paperless_invoice(picking)
                except Exception as e:
                    # Log the error but don't block the validation
                    self.env.user.notify_warning(
                        message=f"Failed to send paperless invoice: {str(e)}",
                        title="UPS Paperless Invoice",
                        sticky=True,
                    )
        return res
