# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Stock Picking Delivery Rate",
    "summary": "Adds a concept of rate quotes for stock pickings",
    "version": "10.0.1.0.0",
    "category": "Inventory, Logistics, Warehousing",
    "website": "https://laslabs.com/",
    "author": "LasLabs, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
        "delivery",
        'purchase',
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/delivery_carrier_view.xml",
        "views/stock_picking_view.xml",
        "views/stock_picking_rate_view.xml",
        'wizards/stock_picking_rate_purchase_view.xml',
    ],
}
