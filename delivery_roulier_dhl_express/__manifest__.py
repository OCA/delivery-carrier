# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier DHL Express",
    "version": "14.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "DHL Express integration through Roulier API",
    "category": "Warehouse",
    "depends": [
        "delivery_roulier_option",  # for customs specific roulier code (yeah...)
        "stock_quant_package_dimension",  # dhl requires package dimensions
        "intrastat_base",  # for customs declaration
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/carrier_account_views.xml",
        "data/product.product.xml",
        "data/delivery_carrier.xml",
    ],
    "maintainers": ["paradoxxxzero"],
    "demo": [
        "demo/carrier_account.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
