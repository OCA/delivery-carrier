# Copyright 2024 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery State Manual",
    "summary": "Manually edit the delivery state of pickings",
    "version": "16.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Sygel, Odoo Community Association (OCA)",
    "maintainers": ["tisho99"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery_state",
    ],
    "data": [
        "views/delivery_carrier_views.xml",
        "views/stock_picking_views.xml",
    ],
}
