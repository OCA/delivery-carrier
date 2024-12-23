# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Package Fees",
    "summary": "Add fees on sales order for delivered packages",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "installable": True,
    "license": "AGPL-3",
    "depends": ["stock_delivery"],
    "data": ["views/delivery_carrier_views.xml", "security/ir.model.access.csv"],
}
