# Copyright 2015 FactorLibre (http://www.factorlibre.com)
#        Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class ManifestWizard(models.TransientModel):
    _name = "manifest.wizard"
    _description = "Delivery carrier manifest wizard"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        required=True,
    )
    from_date = fields.Datetime(required=True)
    to_date = fields.Datetime()
    file_out = fields.Binary("Manifest")
    filename = fields.Char("File Name")
    notes = fields.Text("Result")
    state = fields.Selection(
        [("init", "Init"), ("file", "File"), ("end", "END")],
        default="init",
    )

    def get_manifest_file(self):
        raise NotImplementedError(
            _("Manifest not implemented for '%s' carrier.")
            % self.carrier_id.delivery_type
        )
