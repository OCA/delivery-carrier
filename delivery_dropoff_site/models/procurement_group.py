# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockRule(models.Model):
    """A rule describe what a procurement should do; produce, buy, move, ..."""

    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        """The purpose of this method is to be override in order to easily add
        fields from procurement 'values' argument to move data.
        """
        ret = super(StockRule, self)._get_custom_move_fields()
        ret.append("final_shipping_partner_id")
        return ret
