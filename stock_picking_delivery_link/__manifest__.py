# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Picking Delivery Link",
    "summary": "Adds link to the delivery on all intermediate operations.",
    "version": "16.0.1.1.4",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "category": "Warehouse Management",
    "depends": ["stock", "delivery"],
    "data": ["views/stock_picking.xml", "views/stock_picking_type.xml"],
    "installable": True,
    "license": "AGPL-3",
}
