# Copyright 2012 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection()
    available_option_ids = fields.One2many(
        comodel_name="delivery.carrier.option",
        inverse_name="carrier_id",
        string="Option",
        context={"active_test": False},
    )

    def default_options(self):
        """ Returns default and available options for a carrier """
        options = self.env["delivery.carrier.option"].browse()
        for available_option in self.available_option_ids:
            if available_option.mandatory or available_option.by_default:
                options |= available_option
        return options

    def send_shipping(self, pickings):
        """Handle labels and  if we have them. Expected format is {'labels': [{}, ...]}
        The dicts are input for stock.picking#attach_label"""
        result = super().send_shipping(pickings)
        for result_dict, picking in zip(result, pickings):
            for label in result_dict.get("labels", []):
                picking.attach_shipping_label(label)
        return result
