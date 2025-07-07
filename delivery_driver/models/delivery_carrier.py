# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    driver_id = fields.Many2one(
        "res.partner",
        "Default Driver",
        domain="[('is_company', '=', False)]",
        help="Default driver for this delivery method",
    )

    @api.model_create_multi
    def create(self, vals_list):
        carriers = super().create(vals_list)
        partners = carriers.mapped("driver_id")
        if partners:
            partners.write({"is_driver": True})
        return carriers

    def write(self, vals):
        partner = self.env["res.partner"].browse(vals.get("driver_id", False))
        if partner:
            partner.write({"is_driver": True})
        return super().write(vals)
