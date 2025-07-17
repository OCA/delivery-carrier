# Copyright - 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import html

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    tracking_url_clickable = fields.Html(
        compute="_compute_tracking_url_clickable",
        readonly=True,
    )

    @api.depends(
        "carrier_id.default_tracking_url",
        "carrier_id.tracking_number_separator",
        "carrier_tracking_ref",
    )
    def _compute_tracking_url_clickable(self):
        for picking in self:
            base_url = picking.carrier_id.default_tracking_url
            tracking_ref = picking.carrier_tracking_ref
            separator = picking.carrier_id.tracking_number_separator
            if not base_url or not tracking_ref:
                picking.tracking_url_clickable = False
                continue
            tracking_refs = (
                tracking_ref.split(separator) if separator else [tracking_ref]
            )
            links = []
            for ref in tracking_refs:
                ref = ref.strip()
                if ref:
                    # Extra security check here
                    safe_ref = html.escape(ref)
                    safe_url = html.escape(f"{base_url}{ref}")
                    links.append(f'<a href="{safe_url}" target="_blank">{safe_ref}</a>')

            picking.tracking_url_clickable = "<br/>".join(links) if links else False
