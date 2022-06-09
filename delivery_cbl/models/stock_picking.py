# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def cbl_generate_file(self):
        for picking in self:
            txt = picking.carrier_id.generate_cbl_file(picking)
            if isinstance(txt, str):
                txt.encode()
            txt_name = picking._get_cbl_filename(picking.name)
            picking.message_post(
                body=_("Generated CBL file."), attachments=[(txt_name, txt)]
            )

    def _get_cbl_filename(self, name):
        self.ensure_one()
        return "cbl_{}.txt".format(name).replace(" ", "_").replace("/", "")
