# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Partner Delivery Schedule Zone",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "summary": "Link delivery zones with delivery schedules",
    "author": "Odoo Community Association (OCA), ACSONE SA/NV",
    "website": "https://github.com/OCA/delivery-carrier",
    "license": "AGPL-3",
    "development_status": "Beta",
    "maintainers": ["StephaneMangin"],
    "depends": [
        "partner_delivery_schedule",
        "partner_delivery_zone",
    ],
    "data": [
        "views/partner_delivery_zone.xml",
        "views/delivery_schedule.xml",
    ],
    "installable": True,
}
