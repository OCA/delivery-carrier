# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Free Over Untaxed Price",
    "summary": "Decide if delivery is free over the untaxed price.",
    "version": "18.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery",
    ],
    "data": [
        "views/delivery_carrier_views.xml",
    ],
}
