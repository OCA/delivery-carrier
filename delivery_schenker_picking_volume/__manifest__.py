# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Schenker Picking Volume",
    "summary": "Glue module between delivery_schenker and stock_picking_volume"
    "With this module the transmitted volume is changed,"
    "it uses the computed volume from stock_picking_volume",
    "version": "14.0.1.1.1",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "MT Software, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["delivery_schenker", "stock_picking_volume"],
    "auto_install": True,
}
