# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    zip_option = fields.Selection(
        selection=[
            ("prefix", "Prefixes"),
            ("range", "Ranges"),
        ],
        default="prefix",
    )
    zip_range_ids = fields.One2many(
        comodel_name="delivery.carrier.zip",
        inverse_name="carrier_id",
        string="ZIP codes",
    )

    def _match_address(self, partner):
        """Match as well by zip intervals if they are present."""
        res = super()._match_address(partner)  # it has self.ensure_one()
        if res and self.zip_option == "range" and self.zip_range_ids:
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
    zip_from = fields.Char(required=True)
    zip_to = fields.Char(required=True)
    name = fields.Char(compute="_compute_name")

    @api.depends("zip_from", "zip_to")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.zip_from} - {record.zip_to}"
