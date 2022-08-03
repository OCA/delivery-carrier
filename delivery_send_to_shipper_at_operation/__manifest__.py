# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
{
    "name": "Delivery Send To Shipper at Operation",
    "summary": "Send delivery notice to the shipper from any operation.",
    "version": "14.0.1.0.1",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        # core
        "stock",
        "delivery",
        # OCA/delivery-carrier
        "stock_picking_delivery_link",
    ],
    "data": ["views/delivery_carrier.xml", "views/stock_picking.xml"],
}
