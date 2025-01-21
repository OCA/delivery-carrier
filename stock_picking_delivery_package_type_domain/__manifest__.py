# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Delivery Package Type Domain",
    "summary": """
        This module will allow to extend the domain to filter package type
        selection in 'Choose Delivery Package' wizard""",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": [
        "delivery",
    ],
    "data": [
        "wizards/choose_delivery_package.xml",
    ],
}
