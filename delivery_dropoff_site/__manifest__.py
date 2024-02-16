# Copyright (C) 2014 - Today: Akretion (http://www.akretion.com)
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author Aymeric Lecomte <aymeric.lecomte@akretion.com>
# @author David BEAL <david.beal@akretion.com>
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Drop-off Sites",
    "version": "14.0.1.0.0",
    "author": "Akretion,GRAP,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "summary": "Send goods to sites in which customers come pick up package",
    "category": "Delivery",
    "depends": ["delivery", "base_geolocalize", "resource", "sale_stock"],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "security/ir.model.access.csv",
        "views/view_dropoff_site.xml",
        "views/view_sale_order.xml",
        "views/view_stock_picking.xml",
        "views/view_delivery_carrier.xml",
    ],
    "demo": [
        "demo/res_groups.xml",
        "demo/resource_calendar.xml",
        "demo/delivery_carrier.xml",
        "demo/dropoff_site.xml",
    ],
    "images": [
        "static/description/dropoff_site_form.png",
        "static/description/dropoff_site_form_calendar.png",
        "static/description/dropoff_site_tree.png",
        "static/description/sale_order_form.png",
    ],
    "installable": True,
}
