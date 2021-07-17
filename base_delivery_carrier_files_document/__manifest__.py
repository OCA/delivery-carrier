# Copyright 2012 Camptocamp SA
# Copyright 2021 Sunflower IT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Store carrier files as attachments",
    "version": "14.0.1.0.0",
    "category": "Generic Modules/Warehouse",
    "summary": """
    Allow to store carrier files as attachments.
    Auto-install when the module Document and
    Base Delivery Carrier Files are installed.
    """,
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Sunflower IT, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["base_delivery_carrier_files", "attachment_indexation"],
    "demo": ["demo/carrier_file_demo.xml"],
    "installable": True,
    "auto_install": True,
}
