# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models

from odoo.addons.web.controllers.main import clean_action


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_autoprint_report_actions(self):
        report_actions = super()._get_autoprint_report_actions()
        pickings_to_print = self.filtered(
            lambda p: p.picking_type_id.auto_print_shipping_labels
            and p.shipping_label_ids
        )
        if pickings_to_print:
            action = pickings_to_print.action_print_shipping_labels()
            report_actions.append(action)
        return report_actions

    def action_print_shipping_labels(self):
        action = self.env.ref(
            "stock_picking_delivery_label_to_printer.shipping_label_report_action"
        ).report_action(self.ids, config=False)
        action["data"] = {"shipping_label_ids": self.shipping_label_ids.ids}
        clean_action(action, self.env)
        return action
