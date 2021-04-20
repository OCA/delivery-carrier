# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def generate_carrier_files(self, auto=True, recreate=False):
        """
        Generates all the files for a list of pickings according to
        their configuration carrier file.
        Does nothing on pickings without carrier or without
        carrier file configuration.
        Generate files only for outgoing pickings.

        :param list ids: list of ids of pickings for which we need a file
        :param auto: specify if we call the method from an automatic action
                     (on process on picking as instance)
                     or called manually from the wizard. When auto is True,
                     only the carrier files set as "auto_export"
                     are exported
        :return: True if successful
        """
        carrier_file_ids = {}
        for picking in self:
            if picking.picking_type_id.code != "outgoing":
                continue
            if not recreate and picking.carrier_file_generated:
                continue
            carrier = picking.carrier_id
            if not carrier:
                continue
            if not carrier.carrier_file_id:
                continue
            if auto and not carrier.carrier_file_id.auto_export:
                continue
            p_carrier_file_id = picking.carrier_id.carrier_file_id.id
            carrier_file_ids.setdefault(p_carrier_file_id, []).append(picking.id)

        carrier_files = self.env["delivery.carrier.file"].browse(
            carrier_file_ids.keys()
        )
        for carrier_file in carrier_files:
            carrier_file.generate_files(carrier_file_ids[carrier_file.id])
        return True

    def _action_done(self):
        result = super(StockPicking, self)._action_done()
        self.generate_carrier_files(auto=True)
        return result

    carrier_file_generated = fields.Boolean(
        "Carrier File Generated",
        readonly=True,
        copy=False,
        help="The file for the delivery carrier has been generated.",
    )
