# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_tracking_ref = fields.Char(
        compute="_compute_carrier_tracking_ref",
        store=True,
        readonly=False,
    )
    package_tracking_required = fields.Boolean(
        related="carrier_id.package_tracking_required",
    )

    @api.depends("move_line_ids.result_package_id.carrier_tracking_ref")
    def _compute_carrier_tracking_ref(self):
        """The references of the packages, as the carrier integrations do
        with several parcels; a delivery without packages keeps the value
        typed by hand."""
        for picking in self:
            refs = picking._get_package_tracking_refs()
            if refs:
                picking.carrier_tracking_ref = ",".join(refs)

    @api.depends("move_line_ids.result_package_id.carrier_tracking_ref")
    def _compute_carrier_tracking_url(self):
        """One tracking link per package: the JSON list of (reference, link)
        the native Tracking button already knows how to show."""
        with_packages = self.filtered(
            lambda picking: picking._get_package_tracking_refs()
        )
        res = super(StockPicking, self - with_packages)._compute_carrier_tracking_url()
        for picking in with_packages:
            trackers = [
                (ref, picking.carrier_id._get_package_tracking_link(ref))
                for ref in picking._get_package_tracking_refs()
            ]
            trackers = [tracker for tracker in trackers if tracker[1]]
            picking.carrier_tracking_url = json.dumps(trackers) if trackers else False
        return res

    def _get_package_tracking_refs(self):
        self.ensure_one()
        refs = []
        for package in self.move_line_ids.result_package_id.sorted("name"):
            if (
                package.carrier_tracking_ref
                and package.carrier_tracking_ref not in refs
            ):
                refs.append(package.carrier_tracking_ref)
        return refs

    def button_validate(self):
        for picking in self.filtered(
            lambda pick: pick.package_tracking_required
            and pick.picking_type_code == "outgoing"
        ):
            missing = picking.move_line_ids.result_package_id.filtered(
                lambda package: not package.carrier_tracking_ref
            )
            if missing:
                raise UserError(
                    self.env._(
                        "%(carrier)s needs a tracking reference on every package of "
                        "%(picking)s. Missing on: %(packages)s",
                        carrier=picking.carrier_id.name,
                        picking=picking.name,
                        packages=", ".join(missing.mapped("name")),
                    )
                )
        return super().button_validate()
