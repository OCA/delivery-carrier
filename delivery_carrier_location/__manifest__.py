# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier Location",
    "summary": "Integrates delivery with base_location",
    "version": "14.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["ivantodorovich"],
    "license": "AGPL-3",
    "depends": [
        "delivery_carrier_city",
        "base_location",
    ],
    "data": [
        "views/delivery_carrier.xml",
    ],
}
