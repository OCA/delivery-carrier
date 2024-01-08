# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "Delivery Carrier Manual Weight",
    "summary": """
        Allow setting weight and shipping weight in stock transfers manually
        based on carrier.
    """,
    "version": "16.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "ForgeFlow,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "delivery",
    ],
    "data": ["views/delivery_view.xml"],
    "application": False,
    "installable": True,
}
