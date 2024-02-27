# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Delivery Driver",
    "summary": "Allow choose driver in delivery methods",
    "version": "16.0.1.1.0",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["EmilioPascual", "rafaelbn"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery",
    ],
    "data": [
        "views/delivery_carrier.xml",
        "views/stock_picking.xml",
        "views/stock_move_line.xml",
        "views/res_partner.xml",
    ],
}
