# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
{
    "name": "Delivery Indications by Customer to Carrier",
    "summary": "Send delivery notice to the shipper from any operation.",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sales_team", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner.xml",
        "views/res_partner_delivery_info.xml",
        "views/menus.xml",
    ],
}
