# Copyright 2024 Therp BV (<https://therp.nl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools.barcode import get_barcode_check_digit


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def _get_python_eval_context(self, number_next):
        res = super()._get_python_eval_context(number_next)
        # This function can be used to calculate the value of the
        # check digit at the end of a barcode.
        res.update(
            {
                "get_barcode_check_digit": get_barcode_check_digit,
            }
        )
        return res
