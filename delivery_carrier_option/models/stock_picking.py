# Copyright 2012-2015 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    option_ids = fields.Many2many(
        comodel_name="delivery.carrier.option",
        string="Options",
        compute="_compute_option_ids",
        store=True,
        readonly=False,
    )

    @api.depends("carrier_id")
    def _compute_option_ids(self):
        for picking in self:
            picking.option_ids = picking._get_default_options()

    def _get_default_options(self):
        self.ensure_one()
        default_options = []
        if self.carrier_id:
            default_options = self.carrier_id.default_options()
        return default_options

    @api.onchange("option_ids")
    def onchange_option_ids(self):
        if not self.carrier_id:
            return
        carrier = self.carrier_id
        current_options = options = self.option_ids
        for available_option in carrier.available_option_ids:
            if (
                available_option.mandatory
                and available_option.id not in self.option_ids.ids
            ):
                options |= available_option
        if current_options != options:
            self.option_ids = options
