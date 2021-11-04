# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Gefco",
    "summary": "Integrate Gefco",
    "version": "13.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["delivery", "delivery_package_number", "delivery_carrier_partner"],
    "data": [
        "security/ir.model.access.csv",
        "views/delivery_carrier_view.xml",
        "views/stock_picking_view.xml",
        "views/gefco_destination_view.xml",
        "report/picking_templates.xml",
        "report/stock_report_views.xml",
    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
