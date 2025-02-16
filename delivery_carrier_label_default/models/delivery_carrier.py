# Copyright 2012 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def alternative_send_shipping(self, pickings):
        default_label = pickings.generate_default_label()
        labels = []
        for package in pickings.package_ids:
            pack_label = default_label.copy()
            pack_label["tracking_number"] = package.id
            labels.append(pack_label)
        return [
            {
                "exact_price": pickings.carrier_price,
                "tracking_number": pickings.package_ids,
                "labels": labels,
            }
        ]
