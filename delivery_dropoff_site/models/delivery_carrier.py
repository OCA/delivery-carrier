# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    with_dropoff_site = fields.Boolean(string="With Drop-off Sites")

    dropoff_site_ids = fields.One2many(
        comodel_name="dropoff.site",
        inverse_name="carrier_id",
        string="Drop-off Sites",
    )
