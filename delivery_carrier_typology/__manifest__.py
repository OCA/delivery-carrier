# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier Typology",
    "summary": "Add a typology to delivery carriers",
    "version": "16.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": ["Kev-Roche"],
    "application": False,
    "installable": True,
    "depends": [
        "delivery",
    ],
    "data": [
        "views/delivery_carrier.xml",
        "views/delivery_carrier_typology.xml",
        "security/ir.model.access.csv",
        "wizard/choose_delivery_carrier.xml",
    ],
}
