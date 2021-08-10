# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Carrier labels for paazl",
    "summary": "Print carrier labels for paazl",
    "version": "12.0.1.1.1",
    "development_status": "Beta",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["base_delivery_carrier_label"],
    "data": [
        "data/ir_config_parameter.xml",
        "data/delivery_carrier.xml",
        "data/delivery_carrier_template_option.xml",
        "views/carrier_account.xml",
    ],
    "demo": [],
    "external_dependencies": {"python": ["zeep"]},
}
