# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Estimated Package Quantity By Weight",
    "summary": """
        Compute the amount of packages a picking out should have depending on the
        weight of the products and the limit fixed by the carrier""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "depends": ["stock_delivery"],
    "data": ["views/delivery_carrier_views.xml", "views/stock_picking_views.xml"],
    "installable": True,
}
