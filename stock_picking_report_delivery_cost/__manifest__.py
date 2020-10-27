# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery cost in Picking Reports",
    "summary": "Show delivery cost in delivery slip and picking operations " " reports",
    "version": "13.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["delivery"],
    "data": ["report/report_shipping.xml", "report/report_deliveryslip.xml"],
}
