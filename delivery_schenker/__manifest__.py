# Copyright 2021 Tecnativa - David Vidal
# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Schenker",
    "summary": "Delivery Carrier implementation for DB Schenker API",
    "version": "14.0.1.1.2",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Studio73, Odoo Community Association (OCA)",
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
