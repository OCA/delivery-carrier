# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Carrier labels - Stock Batch Picking (link)",
    "version": "14.0.1.0.2",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainer": "Camptocamp",
    "category": "Carrier",
    "complexity": "normal",
    "depends": ["base_delivery_carrier_label", "stock_picking_batch_extended"],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "data/ir.config_parameter.xml",
        "views/stock_batch_picking.xml",
        "security/ir.model.access.csv",
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
