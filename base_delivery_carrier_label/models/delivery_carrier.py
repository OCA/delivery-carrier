# Copyright 2012 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    available_option_ids = fields.One2many(
        comodel_name="delivery.carrier.option",
        inverse_name="carrier_id",
        string="Option",
        context={"active_test": False},
    )

    def alternative_send_shipping(self, pickings):
        return {}

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
        result = None
        # We could want to generate labels calling a method that does not depend
        # on one specific delivery_type.
        # For instance, if we want to generate a default label in case there are not
        # carrier
        # we may want to call another method not based on any delivery_type.
        # or at the contrary, we could call a common method for multiple delivery_type
        # for instance, in delivery_roulier, the same method is always called for any
        # carrier implemented in roulier lib.
        if pickings.carrier_id:
            result = super().send_shipping(pickings)
        if not result:
            result = self.alternative_send_shipping(pickings)
        for result_dict, picking in zip(result, pickings):
            for label in result_dict.get("labels", []):
                picking.attach_shipping_label(label)
        return result
