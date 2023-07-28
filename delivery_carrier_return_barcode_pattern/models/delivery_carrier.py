# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

HELP_RETURN_BARCODE_PATTERN = """
    This pattern can be used to parse a return barcode from the carrier.
    This has to be a valid regular expression.

    Example for barcode containing only the sales order reference: (?P<origin>.*)
    See https://docs.python.org/3/library/re.html
"""


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    return_barcode_pattern = fields.Char(help=HELP_RETURN_BARCODE_PATTERN)

    @api.constrains("return_barcode_pattern")
    def _constrains_return_barcode_pattern(self):
        for record in self:
            if record.return_barcode_pattern:
                try:
                    re.compile(record.return_barcode_pattern)
                except (re.error):
                    raise ValidationError(
                        _("Return Barcode Pattern must be a valid regular expression")
                    )

    def _get_origin_from_barcode(self, barcode):
        """Return a list of strings, parsed with carrier return barcode patterns.

        If no pattern matched the barcode, it will return an empty set.
        """
        pattern_query, args = self._get_pattern_query()
        self.flush()
        self.env.cr.execute(pattern_query, args)
        patterns = [row[0] for row in self.env.cr.fetchall()]
        res = set()
        for pattern in patterns:
            match = re.match(pattern, barcode)
            if match:
                res.add(match.group("origin"))
        return list(res)

    def _get_pattern_query(self):
        pattern_query = """
            SELECT DISTINCT(trim(return_barcode_pattern))
            FROM delivery_carrier
            WHERE COALESCE(trim(return_barcode_pattern), '') != ''
        """
        ids = ()
        if self.ids:
            pattern_query += "AND id IN %s"
            ids = tuple(self.ids)
        pattern_query += ";"
        return (pattern_query, [ids])
