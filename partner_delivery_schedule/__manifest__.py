# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Partner Delivery Schedule",
    "summary": "Set on partners a schedule for delivery goods",
    "version": "14.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery"],
    "data": [
        "security/ir.model.access.csv",
        "views/partner_delivery_schedule_view.xml",
        "views/res_partner_view.xml",
        "views/report_shipping.xml",
    ],
}
