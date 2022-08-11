# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _check_required_package_measurement(self):
        """Check the required measurement on destination pacakges.

        If package is None all result packages on the stock pickings are checked
        otherwise only the one
        """
        packages = self.move_line_ids.mapped("result_package_id")
        packages._check_required_dimension()

    def button_validate(self):
        self._check_required_package_measurement()
        return super().button_validate()
