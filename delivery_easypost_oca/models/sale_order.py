from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_delivery_line(self, carrier, price_unit):
        sol = super()._create_delivery_line(carrier=carrier, price_unit=price_unit)
        carrier_name = (
            f" - {self.easypost_oca_carrier_name}"
            if self.easypost_oca_carrier_name
            else ""
        )
        sol.name = f"{sol.name}{carrier_name}"
        return sol
