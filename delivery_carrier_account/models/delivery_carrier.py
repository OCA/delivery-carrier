# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    carrier_account_id = fields.Many2one(
        "carrier.account",
        string="Account",
        company_dependent=True,
        domain="[('delivery_type', '=', delivery_type)]",
    )
