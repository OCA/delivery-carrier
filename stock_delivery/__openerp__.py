# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Delivery",
    "summary": "Add additional delivery logic to stock",
    "version": "9.0.1.2.1",
    "category": "Inventory, Logistics, Warehousing",
    "website": "https://laslabs.com/",
    "author": "LasLabs",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
        "delivery",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_delivery_label_view.xml",
        "views/stock_delivery_pack_template_view.xml",
        "views/stock_delivery_pack_view.xml",
        "views/stock_menu.xml",
        "views/stock_picking_view.xml",
        'views/stock_delivery_label_report.xml',
        'wizards/stock_delivery_new_view.xml',
        "data/decimal_precision_data.xml",
    ],
}
