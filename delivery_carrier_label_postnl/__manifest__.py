# Copyright 2021 George Daramouskas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "PostNL Delivery Carrier",
    "summary": "PostNL Delivery Carrier and integration",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "<george.daramouskas@gmail.com>, Odoo Community Association (OCA)",
    "maintainers": ["daramousk"],
    "license": "AGPL-3",
    "application": False,
    "external_dependencies": {
        "python": ["postnl_service_shipment"],
    },
    "depends": [
        "base",
        "base_address_extended",
        "base_delivery_carrier_label",
    ],
    "data": [
        "data/delivery_carrier.xml",
        "data/ir_config_parameter.xml",
    ],
}
