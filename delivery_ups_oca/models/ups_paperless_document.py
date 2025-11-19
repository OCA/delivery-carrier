# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class UpsPaperlessDocument(models.Model):
    _name = "ups.paperless.document"
    _description = "UPS Paperless Document"

    ups_paperless_file = fields.Binary()
    file_name = fields.Char()
    ups_document_type = fields.Selection(
        [
            ("001", "Authorization Form"),
            ("002", "Commercial Invoice"),
            ("003", "Certificate of Origin"),
            ("004", "Export Accompanying Document"),
            ("005", "Export License"),
            ("006", "Import Permit"),
            ("007", "One Time NAFTA"),
            ("008", "Other Document"),
            ("009", "Power of Attorney"),
            ("010", "Packing List"),
            ("011", "SED Document"),
            ("012", "Shipper Letter of Instruction"),
            ("013", "Declaration"),
        ],
        string="Document Type",
        help="The total number of documents allowed per file or per shipment is 13",
        required=True,
    )
    ups_stock_picking_id = fields.Many2one("stock.picking")

    def ups_paperless_file_download(self):
        return {
            "type": "ir.actions.act_url",
            "name": "contract",
            "url": (
                f"/web/content/ups.paperless.document/{self.id}"
                f"/ups_paperless_file/{self.file_name}?download=true"
            ),
        }
