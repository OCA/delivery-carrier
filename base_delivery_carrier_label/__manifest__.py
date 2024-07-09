# Copyright 2013-2015 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Base module for carrier labels",
    "version": "17.0.1.0.1",
    "author": "Camptocamp,Akretion,Odoo Community Association (OCA)",
    "maintainer": "Camptocamp",
    "category": "Delivery",
    "depends": [
        "stock_delivery",
        "delivery_carrier_info",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/delivery.xml",
        "views/stock.xml",
        "views/res_config.xml",
        "security/ir.model.access.csv",
        "wizard/manifest_wizard_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}
