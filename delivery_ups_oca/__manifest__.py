# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery UPS OCA",
    "summary": "Integrate UPS webservice",
    "version": "13.0.1.0.4",
    "development_status": "Production/Stable",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Hunki Enterprises BV, Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "excludes": ["delivery_ups"],
    "depends": [
        "delivery",
        "delivery_package_number",
        "delivery_price_method",
        "delivery_state",
    ],
    "data": ["data/product_packaging_data.xml", "views/delivery_carrier_view.xml"],
    "demo": [],
}
