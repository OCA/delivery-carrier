# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ups_cod_amount = fields.Char(
        "UPS COD Amount", help="UPS COD Price", readonly=True, copy=False
    )
    document_id = fields.Char(
        "DocumentID", help="Forms History Document ID", readonly=True, copy=False
    )
    ups_description = fields.Char("UPS Description", help="UPS Description", copy=False)
    ups_paperless_document = fields.One2many(
        "ups.paperless.document", "ups_stock_picking_id", string="Paperless Document"
    )
    ups_paperless_auto_send = fields.Boolean(
        string="Automatically Send", help="True if you need to Ups Paperless Invoice"
    )

    def ups_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "ups" or not tracking_ref:
            return
        return self.carrier_id.ups_get_label(tracking_ref)

    def generate_paperless_invoice(self):
        return self.carrier_id.ups_paperless_invoice_provider(self)

    @api.onchange("carrier_id", "partner_id")
    def _onchange_ups_paperless_auto_send(self):
        for rec in self:
            if (
                rec.carrier_id.delivery_type == "ups"
                and rec.partner_id
                and rec.partner_id.country_id
                in rec.carrier_id.country_groups.mapped("country_ids")
            ):
                rec.ups_paperless_auto_send = True
            else:
                rec.ups_paperless_auto_send = False

    @api.model_create_multi
    def create(self, vals_list):
        """Override to set ups_paperless_auto_send based on country group"""
        pickings = super().create(vals_list)
        for picking in pickings:
            if (
                picking.carrier_id
                and picking.carrier_id.delivery_type == "ups"
                and picking.partner_id
                and picking.partner_id.country_id
                in picking.carrier_id.country_groups.mapped("country_ids")
            ):
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
                and not picking.document_id
                and picking.ups_paperless_document
            ):
                try:
                    picking.carrier_id.ups_paperless_invoice_provider(picking)
                except Exception as e:
                    # Log the error but don't block the validation
                    self.env.user.notify_warning(
                        message=f"Failed to send paperless invoice: {str(e)}",
                        title="UPS Paperless Invoice",
                        sticky=True,
                    )
        return res
