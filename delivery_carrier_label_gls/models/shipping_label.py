# coding: utf-8
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class ShippingLabel(models.Model):

    _inherit = "shipping.label"

    @api.model
    def _get_file_type_selection(self):
        """Adds GLS supported file types."""
        res = super(ShippingLabel, self)._get_file_type_selection()
        existing_formats = {t[0] for t in res}
        gls_formats = self.env["delivery.carrier"]._fields["gls_label_format"].selection
        for key, name in gls_formats:
            if key not in existing_formats:
                res.append((key, name))
        return res
