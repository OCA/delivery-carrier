# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DelivereaState(models.Model):
    _name = "deliverea.state"

    code = fields.Char("Deliverea State Code")
    state = fields.Char("Deliverea State")
    delivery_state = fields.Selection(
        selection=[
            ("shipping_recorded_in_carrier", "Shipping recorded in carrier"),
            ("in_transit", "In transit"),
            ("canceled_shipment", "Canceled shipment"),
            ("incidence", "Incidence"),
            ("customer_delivered", "Customer delivered"),
            ("warehouse_delivered", "Warehouse delivered"),
        ],
        string="Carrier State",
    )
