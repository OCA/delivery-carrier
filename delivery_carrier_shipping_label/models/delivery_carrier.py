# Copyright 2012 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def send_shipping(self, pickings):
        """Handle labels and  if we have them. Expected format is {'labels': [{}, ...]}
        The dicts are input for stock.picking#attach_label"""
        result = super().send_shipping(pickings)
        if result:
            for result_dict, picking in zip(result, pickings, strict=False):
                for label in result_dict.get("labels", []):
                    picking.attach_shipping_label(label)
        return result
