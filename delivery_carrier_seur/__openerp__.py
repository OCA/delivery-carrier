# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Seur Deliveries WebService",
    "summary": "Allows to generate shipping label for SEUR shipments.",
    "version": "8.0.1.0.0",
    "category": "Delivery",
    "website": "http://factorlibre.com",
    "author": "FactorLibre, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ['seur'],
    },
    "depends": [
        "delivery",
        "base_delivery_carrier_label",
    ],
    "data": [
        "security/ir.model.access.csv",
        "view/seur_config_view.xml",
        "view/delivery_view.xml",
        "view/stock_view.xml"
    ],
    "demo": [],
    "qweb": []
}
