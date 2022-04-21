# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Multiple ZIP intervals for the same delivery method",
    "version": "13.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["delivery"],
    "data": ["security/ir.model.access.csv", "views/delivery_carrier_view.xml"],
    "post_init_hook": "post_init_hook",
}
