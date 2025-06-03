# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Delivery Carrier Picking Valid",
    "summary": "Checks if a transfer matches carrier requirements",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "depends": [
        "stock_delivery",
        "stock_picking_volume",
    ],
}
