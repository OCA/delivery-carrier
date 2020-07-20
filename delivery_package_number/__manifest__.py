# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Picking Package Number",
    "summary": "Set or compute number of packages for a picking",
    "version": "12.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "delivery",
    ],
    "data": [
        "views/stock_picking_views.xml",
        "wizard/stock_immediate_transfer_views.xml",
    ],
}
