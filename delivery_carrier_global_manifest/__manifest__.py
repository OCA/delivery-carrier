# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Carrier Global Manifest",
    "summary": "Manifest files for all carriers",
    "version": "17.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Sygel, Odoo Community Association (OCA)",
    "maintainers": ["tisho99"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_delivery_carrier_label",
    ],
    "data": [
        "report/manifest_wizard_view.xml",
        "views/delivery_carrier_view.xml",
        "wizards/manifest_wizard_view.xml",
    ],
}
