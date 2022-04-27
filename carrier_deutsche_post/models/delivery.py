from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    carrier_account_id = fields.Many2one("carrier.account", "Carrier Account")
    product_code = fields.Char()
    delivery_type = fields.Selection(
        selection_add=[("deutsche_post", "Deutsche Post")],
        ondelete={
            "deutsche_post": lambda recs: recs.write(
                {
                    "delivery_type": "fixed",
                    "fixed_price": 0,
                }
            )
        },
        help="Carrier type (combines several delivery methods)",
    )

    @api.onchange("carrier_account_id")
    def onchange_carrier_account_id(self):
        if self.carrier_account_id:
            self.delivery_type = self.carrier_account_id.delivery_type
