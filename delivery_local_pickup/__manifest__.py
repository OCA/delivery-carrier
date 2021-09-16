# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Local pickup",
    "version": "13.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["delivery", "website"],
    "data": [
        "views/assets.xml",
        "views/delivery_carrier_view.xml",
        "views/website_templates.xml",
    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
