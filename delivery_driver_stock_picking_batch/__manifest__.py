# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Delivery Driver Stock Picking Batch",
    "summary": "Add drivers from delivery in stock picking batch",
    "version": "18.0.1.0.1",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["EmilioPascual"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_picking_batch",
        "delivery_driver",
    ],
    "data": [
        "views/stock_picking_batch.xml",
    ],
}
