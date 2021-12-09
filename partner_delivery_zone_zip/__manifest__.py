# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Partner Delivery Zone Zip",
    "summary": """
        Allows to define a set of zip codes to a delivery zone""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": [
        "partner_delivery_zone",
    ],
    "data": [
        "security/partner_delivery_zone.xml",
        "views/partner_delivery_zone.xml",
    ],
}
