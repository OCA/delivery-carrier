# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Category",
    "summary": "Adds category for delivery carrier",
    "version": "13.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Operations/Inventory/Delivery",
    "depends": ["delivery"],
    "website": "http://www.camptocamp.com",
    "data": ["security/ir.model.access.csv", "views/delivery_carrier_views.xml"],
    "installable": True,
}
