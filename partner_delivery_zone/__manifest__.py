# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Partner Delivery Zone",
    "summary": "Set on partners a zone for delivery goods",
    "version": "13.0.1.2.0",
    "development_status": "Beta",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Pesol, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/partner_delivery_zone_view.xml",
        "views/res_partner_view.xml",
        "views/sale_order_view.xml",
        "views/stock_picking_view.xml",
        "views/report_deliveryslip.xml",
        "views/report_shipping.xml",
    ],
}
