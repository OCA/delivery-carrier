# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

{
    "name": "Sendcloud Return Portal",
    "summary": "Create warehouse operations from Sendcloud return portal returns",
    "version": "19.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "arielbarreiros96, Odoo Community Association (OCA)",
    "maintainers": ["arielbarreiros96"],
    "license": "LGPL-3",
    "installable": True,
    "depends": ["delivery_sendcloud_oca", "sale_stock"],
    "data": [
        "data/product_data.xml",
        "data/cron.xml",
        "views/res_config_settings_view.xml",
        "views/sendcloud_return_view.xml",
    ],
}
