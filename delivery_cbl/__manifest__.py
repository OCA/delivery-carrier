# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Delivery CBL",
    "summary": "Generate CBL file when validating a picking",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "author": "Studio73, Odoo Community Association (OCA)",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": ["delivery_package_number"],
    "data": ["views/delivery_carrier_views.xml", "views/stock_picking_views.xml"],
    "installable": True,
}
