# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Carrier labels - Stock Batch Picking (link)",
    "version": "18.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainer": "Camptocamp",
    "category": "Carrier",
    "complexity": "normal",
    "depends": [
        # Odoo/core
        "stock_delivery",
        # OCA/delivery-carrier
        "delivery_carrier_option",
        "delivery_carrier_shipping_label",
        "delivery_carrier_package_info",
        # OCA/stock-logistics-workflow
        "stock_picking_batch_extended",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        # Security
        "security/ir.model.access.csv",
        # Data
        "data/ir.config_parameter.xml",
        # Views
        "views/stock_batch_picking.xml",
        # Wizard
        "wizard/generate_labels_view.xml",
        "wizard/apply_carrier_view.xml",
    ],
    "installable": True,
    "auto_install": True,
    "license": "AGPL-3",
    "application": False,
    "external_dependencies": {
        "python": ["PyPDF2"],
    },
}
