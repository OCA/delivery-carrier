# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Automatic Package",
    "summary": """
        Allows to set a delivery package automatically when sending to shipper.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": [
        "delivery",
    ],
    "data": [
        "views/delivery_carrier.xml",
        "views/res_config_settings.xml",
    ],
}
