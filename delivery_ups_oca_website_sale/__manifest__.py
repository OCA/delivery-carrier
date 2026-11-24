# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery UPS OCA - Website Sale",
    "summary": "Show UPS duties, taxes & fees at checkout",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Nitrokey GmbH, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "delivery_ups_oca",
        "website_sale",
    ],
    "data": [
        "views/website_sale_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "delivery_ups_oca_website_sale/static/src/js/checkout_landed_cost.esm.js",
        ],
    },
    "auto_install": True,
}
