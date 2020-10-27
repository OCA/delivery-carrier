# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    ups_code = fields.Selection(
        [
            ("01", "UPS Letter"),
            ("02", "Customer Supplied Package"),
            ("03", "Tube"),
            ("04", "PAK"),
            ("21", "UPS Express Box"),
            ("24", "UPS 25KG Box"),
            ("25", "UPS 10KG Box"),
            ("30", "Pallet"),
            ("2a", "Small Express Box"),
            ("2b", "Medium Express Box"),
            ("2c", "Large Express Box"),
            ("56", "Flats"),
            ("57", "Parcels"),
            ("58", "BPM"),
            ("59", "First Class"),
            ("60", "Priority"),
            ("61", "Machineables"),
            ("62", "Irregulars"),
            ("63", "Parcel Post"),
            ("64", "BPM Parcel"),
            ("65", "Media Mail"),
            ("66", "BPM Flat"),
            ("67", "Standard Flat"),
        ],
    )
