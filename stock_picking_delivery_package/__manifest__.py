# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Delivery Package",
    "summary": """
        This module allows to define a delivery package elsewhere than on the
        delivery picking""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": [
        "stock_picking_delivery_link",
    ],
    "data": [
        "views/stock_picking_type.xml",
    ],
}
