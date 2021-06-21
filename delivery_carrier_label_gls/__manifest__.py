# coding: utf-8
# © 2015 David BEAL @ Akretion
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Carrier Label GLS",
    "version": "10.0.1.0.0",
    "author": "Acsone,Akretion,Odoo Community Association (OCA)",
    "maintener": "Akretion",
    "category": "Warehouse",
    "summary": "GLS carrier label printing",
    "depends": [
        "base_delivery_carrier_label",
        "partner_helper",
        "document",
        "delivery",
    ],
    "website": "http://www.acsone.eu/",
    "data": [
        "security/ir.model.access.csv",
        "data/cron_end_of_day_report.xml",
        "data/product_product.xml",
        "data/product_packaging.xml",
        "data/delivery_carrier.xml",
        "views/delivery_carrier.xml",
        "views/delivery_report_gls.xml",
        "views/sale_order.xml",
        "views/stock.xml",
        "wizards/delivery_report_gls_wizard.xml",
        "report/report_delivery_report_gls.xml",
        "report/delivery_report_gls_view.xml",
    ],
    "demo": ["demo/delivery_carrier.xml"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "pre_init_hook": "pre_init_hook",
}
