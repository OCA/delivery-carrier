# Copyright 2022 Impulso Diagonal - Javier Colmeiro
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Sending",
    "summary": "Delivery Carrier implementation for Sending API",
    "version": "13.0.1.2.1",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Impulso Diagonal, Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery_package_number", "delivery_state"],
    "external_dependencies": {"python": ["suds"]},
    "data": ["views/delivery_sending_view.xml", "views/stock_picking_views.xml"],
}
