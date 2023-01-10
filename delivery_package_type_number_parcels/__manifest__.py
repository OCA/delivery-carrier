# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Package Type Number Parcels",
    "summary": "Number of parcels in a package type",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": ["delivery"],
    "data": [
        "views/stock_quant_package_views.xml",
        "views/stock_package_type_views.xml",
        "wizards/choose_delivery_package_views.xml",
    ],
    "installable": True,
}
