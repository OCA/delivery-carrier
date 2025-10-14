# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Correos Express",
    "summary": "Delivery Carrier implementation for Correos Express using their API",
    "version": "18.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Studio73, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery_package_number", "delivery_state"],
    "external_dependencies": {"python": ["unidecode"]},
    "data": ["views/delivery_carrier_view.xml", "views/stock_picking_views.xml"],
}
