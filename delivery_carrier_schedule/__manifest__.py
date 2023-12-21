# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Delivery carrier schedule",
    "summary": "Allow to set Availability windows on Carriers",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Sales",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide", "EmilioPascual", "yajo"],
    "license": "LGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["freezegun"]},
    "depends": [
        "delivery",
        "delivery_partner_schedule",
    ],
    "data": [
        "views/delivery_carrier_view.xml",
    ],
}
