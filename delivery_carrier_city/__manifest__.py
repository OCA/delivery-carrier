# Copyright 2021 Camptocamp SA - Iván Todorovich
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier City",
    "summary": "Integrates delivery with base_address_city",
    "version": "15.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["ivantodorovich"],
    "license": "AGPL-3",
    "depends": [
        "delivery",
        "base_address_city",
    ],
    "data": [
        "views/delivery_carrier.xml",
    ],
}
