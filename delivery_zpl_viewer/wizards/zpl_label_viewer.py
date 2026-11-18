# Copyright (c) 2026 Groupe Voltaire
# @author Emilie SOUTIRAS <emilie.soutiras@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
import re

import requests

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

PARAM_PREFIX = "delivery_zpl_viewer"
ALLOWED_DPMM = ("6", "8", "12", "24")
LABELARY_TIMEOUT = 15
MM_PER_INCH = 25.4


class DeliveryZplLabelViewer(models.TransientModel):
    _name = "delivery.zpl.label.viewer"
    _description = "ZPL Label Viewer"

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Transfer",
        required=True,
        ondelete="cascade",
    )
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="ZPL Label",
        domain="[('res_model', '=', 'stock.picking'), "
        "('res_id', '=', picking_id), ('name', '=ilike', '%.zpl')]",
    )
    label_index = fields.Integer(string="Label", default=1)
    label_count = fields.Integer(compute="_compute_preview")
    preview_image = fields.Binary(string="Preview", compute="_compute_preview")
    preview_error = fields.Text(compute="_compute_preview")

    @api.depends("attachment_id", "label_index")
    def _compute_preview(self):
        for wizard in self:
            wizard.update(
                {"label_count": 0, "preview_image": False, "preview_error": False}
            )
            if wizard.attachment_id:
                wizard.update(wizard._render_labelary(wizard.attachment_id.raw))

    def _get_labelary_settings(self):
        params = self.env["ir.config_parameter"].sudo()
        url = params.get_param(f"{PARAM_PREFIX}.labelary_url") or (
            "https://api.labelary.com"
        )
        dpmm = params.get_param(f"{PARAM_PREFIX}.dpmm") or "8"
        if dpmm not in ALLOWED_DPMM:
            dpmm = "8"
        default_size = params.get_param(f"{PARAM_PREFIX}.default_size") or "4x6"
        width, _sep, height = default_size.lower().partition("x")
        return url.rstrip("/"), int(dpmm), float(width), float(height)

    @api.model
    def _get_label_size(self, zpl, dpmm, default_width, default_height):
        dots_per_inch = dpmm * MM_PER_INCH
        width_match = re.search(rb"\^PW(\d+)", zpl)
        height_match = re.search(rb"\^LL(\d+)", zpl)
        width = (
            round(int(width_match.group(1)) / dots_per_inch, 1)
            if width_match
            else default_width
        )
        height = (
            round(int(height_match.group(1)) / dots_per_inch, 1)
            if height_match
            else default_height
        )
        return width, height

    def _render_labelary(self, zpl):
        self.ensure_one()
        if not zpl:
            return {"preview_error": _("The attachment is empty.")}
        url, dpmm, default_width, default_height = self._get_labelary_settings()
        width, height = self._get_label_size(zpl, dpmm, default_width, default_height)
        index = max(self.label_index - 1, 0)
        # flake8: noqa: E231
        endpoint = (
            f"{url}/v1/printers/{dpmm}dpmm/labels" f"/{width:g}x{height:g}/{index}/"
        )
        try:
            response = requests.post(
                endpoint,
                data=zpl,
                headers={
                    "Accept": "image/png",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=LABELARY_TIMEOUT,
            )
        except requests.RequestException as error:
            _logger.warning("Labelary rendering failed on %s: %s", endpoint, error)
            return {
                "preview_error": _("The Labelary service is unreachable: %s") % error
            }
        if not response.ok:
            _logger.warning(
                "Labelary rendering failed on %s: %s %s",
                endpoint,
                response.status_code,
                response.text,
            )
            return {
                "preview_error": _("Labelary could not render the label: %s")
                % response.text
            }
        return {
            "label_count": int(response.headers.get("X-Total-Count") or 1),
            "preview_image": base64.b64encode(response.content),
        }
