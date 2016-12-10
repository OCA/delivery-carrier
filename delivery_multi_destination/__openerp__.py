# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Multiple destinations for the same delivery method",
    "version": "9.0.1.0.0",
    "category": "Delivery",
    "website": "https://www.tecnativa.com/",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "delivery",
    ],
    "data": [
        "views/delivery_carrier_view.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "post_init_hook": "post_init_hook",
}
