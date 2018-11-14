# Copyright 2013-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Default label for carrier labels",
    "summary": "This module defines a basic label to print "
               "when no specific carrier is selected.",
    "version": "11.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "base_delivery_carrier_label",
    ],
    "data": [
        "views/report_default_label.xml",
        "views/reports.xml",
    ],
}
