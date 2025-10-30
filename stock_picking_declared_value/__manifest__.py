# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Picking Declared Value",
    "summary": "Display product declared values on stock pickings from sales orders",
    "version": "18.0.1.0.0",
    "category": "Warehouse",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Nitrokey GmbH, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
        "sale_stock",
        "stock_delivery",
    ],
    "data": [
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/delivery_carrier_views.xml",
    ],
}
