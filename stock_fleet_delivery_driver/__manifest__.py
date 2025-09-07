# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Stock Fleet Delivery Driver",
    "summary": "Allow choose Vehicle in Carriers, Transfers and Batches",
    "version": "18.0.1.0.1",
    "development_status": "Alpha",
    "category": "Inventory/Inventory",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide", "rafaelbn", "EmilioPascual"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_fleet",
        "delivery_stock_picking_batch",
        "delivery_driver",
    ],
    "excludes": [
        "delivery_driver_stock_picking_batch",
    ],
    "data": [
        "views/delivery_carrier_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_batch_views.xml",
        "views/stock_picking_type_views.xml",
        "reports/report_picking_batch.xml",
    ],
}
