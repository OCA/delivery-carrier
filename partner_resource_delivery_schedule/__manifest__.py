# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Partner Resource Delivery Schedule",
    "summary": "Allow to set Availability windows on Partners",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Sales",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide", "EmilioPascual", "yajo"],
    "license": "LGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["freezegun"]},
    "depends": [
        "resource",
        "sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/delivery_schedule_security.xml",
        "views/resource_resource_view.xml",
        "views/resource_calendar_view.xml",
        "views/res_partner_view.xml",
        "views/sale_order_view.xml",
    ],
}
