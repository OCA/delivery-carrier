# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier Typology",
    "version": "14.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "delivery",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/delivery_carrier.xml",
        "views/product.xml",
    ],
    "installable": True,
}
