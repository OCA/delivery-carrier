# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    gefco_destination_id = fields.Many2one(
        comodel_name="gefco.destination",
        string="Gefco Destination",
        compute="_compute_gefco_destination_id",
        store=True,
    )

    @api.depends("partner_id.country_id", "partner_id.zip")
    def _compute_gefco_destination_id(self):
        for item in self:
            if item.partner_id.country_id and item.partner_id.zip:
                item.gefco_destination_id = self.env["gefco.destination"].search(
                    [
                        ("country_code", "=", item.partner_id.country_id.code),
                        ("zip_code", "=", item.partner_id.zip),
                    ],
                    limit=1,
                )
            else:
                item.gefco_destination_id = item.gefco_destination_id

    def _get_gefco_barcode(self, number):
        return "%s%s" % (self.carrier_tracking_ref, str(number + 1).zfill(2))
