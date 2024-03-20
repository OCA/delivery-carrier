# © 2015 David BEAL @ Akretion
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Carrier Label GLS",
    "version": "16.0.1.0.0",
    "author": "Acsone,Akretion,Odoo Community Association (OCA)",
    "maintener": "Akretion",
    "category": "Warehouse",
    "summary": "GLS carrier label printing",
    "depends": [
        "base_delivery_carrier_label",
        "delivery",
        "delivery_carrier_account",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "data/product_product.xml",
        "data/carrier_account.xml",
        "data/delivery_carrier.xml",
        "data/stock_package_type.xml",
        "views/res_config_settings.xml",
        "views/delivery_carrier.xml",
        "views/delivery_report_gls.xml",
        "views/sale_order.xml",
        "views/stock.xml",
        "views/carrier_account.xml",
        "wizards/delivery_report_gls_wizard.xml",
        "report/report_delivery_report_gls.xml",
        "report/delivery_report_gls_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "post_init_hook": "post_init_hook",
}
