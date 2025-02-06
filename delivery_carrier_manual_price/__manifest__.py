# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier Manual Price",
    "summary": "Allow setting manual shipping cost in sale order.",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "ForgeFlow,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "delivery",
    ],
    "data": ["wizard/choose_delivery_carrier_views.xml", "views/delivery_view.xml"],
    "application": False,
    "installable": True,
}
