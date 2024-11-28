# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Roulier Picking Batch",
    "version": "14.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Use roulier in batch picking",
    "category": "Warehouse",
    "depends": [
        "delivery_roulier",
        "stock_picking_batch",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/stock_picking_batch_views.xml",
    ],
    "demo": [],
    "installable": True,
    "license": "AGPL-3",
}
