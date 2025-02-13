# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "Delivery Carrier Package Info",
    "summary": "Add track ref on packages",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "delivery",
    ],
    "data": ["views/stock_quant_package.xml"],
    "application": False,
    "installable": True,
}
