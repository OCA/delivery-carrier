# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Delivery Package Tracking",
    "summary": "One tracking reference per package of a delivery",
    "version": "19.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": ["stock_delivery"],
    "data": [
        "views/delivery_carrier_views.xml",
        "views/stock_package_views.xml",
    ],
    "installable": True,
}
