# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Delivery Schedule Zone",
    "summary": "Assign delivery schedule to sales orders based on partner zone",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Sales/Sales",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["StephaneMangin"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "partner_delivery_schedule_zone",
    ],
    "data": [
        "views/res_config_settings.xml",
        "views/sale_order_view.xml",
    ],
}
