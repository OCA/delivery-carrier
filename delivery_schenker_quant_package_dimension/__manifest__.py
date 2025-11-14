# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Schenker Quant Package Dimension",
    "summary": "Glue module between delivery_schenker and stock_quant_package_dimension"
    "With this module the transmitted package volume is changed,"
    "it uses the computed volume from stock_quant_package_dimension."
    "Also the dimensions length, width and height of a package "
    "getting added to the request",
    "version": "14.0.2.0.1",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "MT Software, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["delivery_schenker", "stock_quant_package_dimension"],
    "auto_install": True,
    "maintainers": ["mt-software-de"],
}
