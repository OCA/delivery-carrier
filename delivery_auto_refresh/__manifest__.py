# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Auto-refresh delivery",
    "summary": "Auto-refresh delivery price in sales orders",
    "version": "14.0.1.1.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery"],
    "data": ["data/ir_config_parameter.xml", "views/sale_order_views.xml"],
}
