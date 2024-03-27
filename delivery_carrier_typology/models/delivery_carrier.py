# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    shipping_means_ids = fields.Many2many(
        comodel_name="delivery.carrier.typology",
        string="Shipping means",
    )

    def available_carriers(self, partner):
        res = super().available_carriers(partner)
        if self.env.context.get("active_model") == "sale.order":
            sale = self.env["sale.order"].browse(self.env.context.get("active_id"))
            prohibited_shipping_means_ids = sale.order_line.mapped(
                "prohibited_shipping_means_ids"
            )
            new_res = self.browse()
            for carrier in res:
                if not set(carrier.shipping_means_ids) & set(
                    prohibited_shipping_means_ids
                ):
                    new_res += carrier
            res = new_res
        return res


class DeliveryCarrierTypology(models.Model):
    _name = "delivery.carrier.typology"
    _description = "Shipping means"

    name = fields.Char(string="Name", required=True, translate=True)
    code = fields.Char(string="Code")
    description = fields.Char(string="Description", translate=True)
    company_id = fields.Many2one("res.company", string="Company")
