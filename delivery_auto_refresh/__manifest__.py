# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Auto-refresh delivery",
    "summary": "Auto-refresh delivery price in sales orders",
    "version": "16.0.2.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery"],
    # Migration Note 17.0: Add dependency to sale_order_carrier_auto_assign
    # "depends": ["delivery", "sale_order_carrier_auto_assign"],
    "data": ["views/sale_order_views.xml", "views/res_config_settings_views.xml"],
}
