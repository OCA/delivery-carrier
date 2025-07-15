# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Delivery Fleet",
    "summary": "Allow choose Vehicle in Carriers, Transfers and Batches",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide", "rafaelbn"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_delivery",
        "stock_fleet",
    ],
    "data": [
        "views/delivery_carrier_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_batch_views.xml",
        "reports/report_picking_batch.xml",
    ],
}
