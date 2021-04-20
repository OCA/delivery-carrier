# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Base Delivery Carrier Files",
    "version": "14.0.1.0.0",
    "category": "Generic Modules/Warehouse",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": ["base", "stock", "delivery"],
    "demo": [
        "data/carrier_file_demo.xml",
    ],
    "data": [
        "views/carrier_file_view.xml",
        "views/stock_view.xml",
        "wizards/generate_carrier_files_view.xml",
        "security/ir.model.access.csv",
    ],
    "summary": "Base module for creation of delivery carrier files",
    "installable": True,
    "auto_install": False,
}
