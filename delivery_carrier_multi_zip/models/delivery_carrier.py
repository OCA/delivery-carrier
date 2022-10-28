# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    zip_range_ids = fields.One2many(
        comodel_name="delivery.carrier.zip",
        inverse_name="carrier_id",
        string="ZIP codes",
    )

    @api.model
    def _convert_zip_to_intervals(self, vals):
        if self.env.context.get("bypass_multi_zip"):
            return
        if vals.get("zip_from") or vals.get("zip_to"):
            vals.setdefault("zip_range_ids", [])
            vals["zip_range_ids"].append(
                (
                    0,
                    0,
                    {
                        "zip_from": vals.get("zip_from", "0") or "0",
                        "zip_to": vals.get("zip_to", "z") or "z",
                    },
                )
            )
            vals.pop("zip_from", False)
            vals.pop("zip_to", False)

    @api.model_create_multi
    def create(self, vals_list):
        """Intercept creation for changing ZIP values to ZIP interval."""
        for vals in vals_list:
            self._convert_zip_to_intervals(vals)
        return super().create(vals_list)

    def write(self, vals):
        """Intercept write for changing ZIP values to ZIP interval."""
        self._convert_zip_to_intervals(vals)
        return super().write(vals)

    def _match_address(self, partner):
        """Match as well by zip intervals if they are present."""
        res = super()._match_address(partner)  # it has self.ensure_one()
        if res and self.zip_range_ids:
            partner_zip = partner.zip or ""
            res = bool(
                self.zip_range_ids.filtered(
                    lambda r: r.zip_from <= partner_zip and r.zip_to >= partner_zip
                )
            )
        return res


class DeliveryCarrierZip(models.Model):
    _name = "delivery.carrier.zip"
    _description = "Delivery destination availability ZIP interval line"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier", ondelete="cascade", index=True
    )
    zip_from = fields.Char("Zip From", required=True)
    zip_to = fields.Char("Zip To", required=True)
    name = fields.Char(compute="_compute_name")

    @api.depends("zip_from", "zip_to")
    def _compute_name(self):
        for record in self:
            record.name = "%s - %s" % (record.zip_from, record.zip_to)
