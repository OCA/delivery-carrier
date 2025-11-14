# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Purchase Label",
    "summary": "Allows printing carrier delivery labels for a dropshipping vendor.",
    "version": "14.0.1.1.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["TDu", "jbaudoux"],
    "installable": True,
    "license": "AGPL-3",
    "depends": ["delivery", "purchase"],
    "data": [
        "data/stock_picking_type.xml",
        "views/delivery_carrier.xml",
        "views/purchase_order_views.xml",
    ],
}
