# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Delivery Package Wizard",
    "summary": "Provides a wizard for the selection of packaging type before "
               "sending a picking to carrier.",
    "version": "10.0.1.0.0",
    "category": "Delivery",
    "website": "https://laslabs.com/",
    "author": "LasLabs, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery",
    ],
    "data": [
        'wizards/delivery_package_wizard_view.xml',
    ],
}
