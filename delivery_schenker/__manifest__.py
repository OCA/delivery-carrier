# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Schenker",
    "summary": "Delivery Carrier implementation for DB Schenker API",
    "version": "13.0.1.0.1",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery_package_number", "delivery_state"],
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "views/delivery_schenker_view.xml",
        "views/stock_picking_views.xml",
        "data/delivery_schenker_data.xml",
    ],
}
