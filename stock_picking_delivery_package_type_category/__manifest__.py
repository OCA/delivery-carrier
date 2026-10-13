# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Delivery Package Type Category",
    "summary": """
        This module allows to filter package types on their category depending
        on the configuration on operation types""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": [
        "stock_package_type_category",
        "stock_picking_delivery_package_type_domain",
    ],
    "data": [
        "views/stock_picking_type.xml",
    ],
}
