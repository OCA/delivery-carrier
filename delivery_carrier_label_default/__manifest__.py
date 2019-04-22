# -*- coding: utf-8 -*-
# Copyright 2013 Camptocamp SA, Yannick Vaucher
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Default label for carrier labels",
    "version": "10.0.1.0.0",
    "author": "Camptocamp,Sunflower IT,Odoo Community Association (OCA)",
    "category": "Warehouse",
    "depends": [
        'base_delivery_carrier_label',
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "reports/report_default_label.xml",
        "reports/report_paper_format.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
