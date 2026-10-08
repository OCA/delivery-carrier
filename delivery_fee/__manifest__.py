# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Delivery Fee",
    "summary": "Charge extra fees on deliveries",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "author": "Moduon, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "maintainers": ["chienandalu", "rafaelbn"],
    "license": "LGPL-3",
    "depends": ["stock_delivery"],
    "data": [
        "views/res_partner_views.xml",
        "views/delivery_carrier_views.xml",
        "views/res_config_settings.xml",
        "reports/delivery_slip_report.xml",
        "reports/invoice_report.xml",
    ],
}
