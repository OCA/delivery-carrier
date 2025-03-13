# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Default label for carrier labels",
    "summary": "This module defines a basic label to print "
    "when no specific carrier is selected.",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "stock_delivery",
        "delivery_carrier_shipping_label",
    ],
    "data": [
        "views/report_default_label.xml",
        "views/reports.xml",
    ],
}
