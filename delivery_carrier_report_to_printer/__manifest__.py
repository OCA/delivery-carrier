# Copyright 2025 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery carrier report to printer",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "license": "AGPL-3",
    "author": "Tecnativa,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/delivery_carrier_view.xml",
        "report/default_delivery_carrier_report.xml",
    ],
    "depends": ["base_report_to_printer", "stock_delivery"],
    "installable": True,
    "maintainers": ["carlos-lopez-tecnativa"],
}
