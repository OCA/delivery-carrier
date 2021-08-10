# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier Category",
    "summary": """
        Adds a category to delivery carriers in order to help users
        classifying them""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "category": "Warehouse",
    "maintainers": ["rousseldenis"],
    "depends": [
        "delivery",
    ],
    "data": [
        "views/delivery_carrier.xml",
        "security/delivery_carrier_category.xml",
        "views/delivery_carrier_category.xml",
        "data/delivery_carrier_category.xml",
    ],
}
