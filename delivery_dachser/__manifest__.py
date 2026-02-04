# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Dachser",
    "summary": "Delivery Carrier implementation for Dachser API",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["delivery_package_number", "delivery_state", "stock_picking_volume"],
    "data": [
        "data/product_packaging_data.xml",
        "views/delivery_carrier_views.xml",
    ],
    "maintainers": ["victoralmau"],
}
