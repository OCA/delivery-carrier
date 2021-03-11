# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Postlogistics Shipping Dangerous Goods",
    "summary": "Declare dangerous goods when generating postlogistics labels",
    "version": "13.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainer": "Camptocamp",
    "license": "AGPL-3",
    "category": "Delivery",
    "complexity": "normal",
    "depends": [
        # OCA/delivery-carrier
        "delivery_postlogistics",
        # OCA/community-data-files
        "l10n_eu_product_adr",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "installable": True,
    "auto_install": False,
    "application": False,
}
