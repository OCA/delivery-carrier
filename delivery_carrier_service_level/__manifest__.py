# Copyright 2013-2020 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Carrier Service Level",
    "summary": "Add service levels to carrier",
    "version": "13.0.1.0.2",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Therp, Odoo Community Association (OCA)",
    "installable": True,
    "license": "AGPL-3",
    "depends": ["delivery"],
    "data": [
        "views/carrier_service_level.xml",
        "views/stock_picking.xml",
        "security/ir.model.access.csv",
    ],
}
