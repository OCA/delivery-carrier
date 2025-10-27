# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import _, models
from odoo.exceptions import ValidationError


class ManifestWizard(models.TransientModel):
    _inherit = "manifest.wizard"

    def _get_cbl_picking(self):
        self.ensure_one()
        search_args = [
            ("carrier_id", "=", self.carrier_id.id),
            ("date_done", ">=", self.from_date),
            ("state", "=", "done"),
            ("cbl_confirmed", "=", True),
            ("carrier_tracking_ref", "!=", False),
        ]
        if self.to_date:
            search_args.append(("date_done", "<=", self.to_date))
        return self.env["stock.picking"].search(search_args)

    def get_manifest_file(self):
        self.ensure_one()
        if self.carrier_id.delivery_type != "cbl":
            return super().get_manifest_file()
        pickings = self._get_cbl_picking()
        if not pickings:
            raise ValidationError(_("There are no pickings to proceed"))
        report_pdf = self.env["ir.actions.report"]._render(
            "delivery_cbl.action_cbl_manifest", [self.id], {"pickings": pickings}
        )[0]
        self.write(
            {
                "state": "file",
                "file_out": base64.b64encode(report_pdf),
                "filename": "manifest-%s.pdf" % (self.carrier_id.name),
            }
        )
        return {
            "name": _("Manifest"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "manifest.wizard",
            "view_id": self.env.ref(
                "base_delivery_carrier_label.manifest_wizard_form"
            ).id,
            "res_id": self.id,
            "target": "new",
        }
