# -*- coding: utf-8 -*-
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery price by category",
    "summary": "Change delivery price based on product's category",
    "version": "10.0.1.0.0",
    "development_status": "Beta",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier/tree/"
               "10.0/delivery_price_by_category",
    "author": "Agile Business Group, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery"
    ],
    "data": [
        "views/delivery_price_rule.xml"
    ]
}
