# Copyright 2019 Tecnativa - Victor M.M. Torres
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Delivery Info Computation",
    "summary": "Improve weight and volume calculation",
    "version": "13.0.1.0.0",
    "category": "Sales, Stock, Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["delivery"],
    "data": [
        "views/stock_picking_views.xml",
        "report/report_shipping.xml",
        "report/report_deliveryslip.xml",
    ],
    "maintainers": ["cubells"],
}
