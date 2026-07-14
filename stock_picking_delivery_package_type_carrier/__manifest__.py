# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Delivery Package Type Carrier",
    "summary": """
        Restricts package type selection and assignment
        to package types dedicated to the picking carrier.""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp SA, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": [
        "stock_picking_delivery_package_type_domain",
    ],
    "data": [
        "views/stock_package_type.xml",
    ],
}
