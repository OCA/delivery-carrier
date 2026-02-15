# Copyright 2026 NICO SOLUTIONS - Nils Coenen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Partner Delivery Schedule Warning",
    "summary": "Add warning for delivery schedule mismatch",
    "version": "19.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "NICO-SOLUTIONS, Odoo Community Association (OCA)",
    "maintainer": "NICO-SOLUTIONS",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["partner_delivery_schedule"],
    "data": [
        "views/stock_picking_view.xml",
    ],
}
