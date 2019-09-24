# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    send_to_transsmart = fields.Boolean('Send To Transsmart?')

    @api.multi
    def do_detailed_transfer(self):
        """
        Send the picking to transsmart if appropriate.
        """
        self.ensure_one()
        if self.send_to_transsmart:
            # TODO how will partial moves be taken care off?
            self.picking_id.action_create_transsmart_document()
        return super(StockTransferDetails, self).do_detailed_transfer()
