# Copyright 2021 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _domain_search_picking_for_assignation_default(self):
        domain = super()._domain_search_picking_for_assignation_default()
        domain.append(("carrier_id", "=", self.sale_line_id.carrier_id.id))
        return domain

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        carrier = self.mapped("sale_line_id.carrier_id")
        if len(carrier) > 1:
            _logger.warning("Moves belongs to different carriers %s" % carrier)
        elif carrier:
            vals["carrier_id"] = carrier[0].id
        return vals

    def _key_assign_picking(self):
        keys = super(StockMove, self)._key_assign_picking()
        return keys + (self.sale_line_id.carrier_id,)
