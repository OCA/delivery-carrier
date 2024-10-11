from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    easypost_oca_shipment_id = fields.Char(tracking=False, copy=False)
    easypost_oca_rate_id = fields.Char(tracking=False, copy=False)
    easypost_oca_carrier_name = fields.Char(tracking=True, copy=False)

    def _create_delivery_line(self, carrier, price_unit):
        sol = super()._create_delivery_line(carrier=carrier, price_unit=price_unit)
        if self.env.context.get("easypost_oca_carrier_name", False):
            carrier_name = (
                f" - {self.easypost_oca_carrier_name}"
                if self.easypost_oca_carrier_name
                else ""
            )
            sol.name = f"{sol.name}{carrier_name}"

        self.with_context(auto_refresh_delivery=True).write(
            {
                "easypost_oca_rate_id": self.env.context.get(
                    "easypost_oca_rate_id", False
                ),
                "easypost_oca_shipment_id": self.env.context.get(
                    "easypost_oca_shipment_id", False
                ),
                "easypost_oca_carrier_name": self.env.context.get(
                    "easypost_oca_carrier_name", False
                ),
            }
        )
        return sol
