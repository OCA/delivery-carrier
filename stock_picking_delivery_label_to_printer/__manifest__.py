# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Print shipping labels on CUPS printer",
    "summary": "Send shipping labels to CUPS printer",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "license": "AGPL-3",
    "category": "Delivery",
    "version": "15.0.1.0.0",
    "depends": [
        "stock_picking_delivery_label_link",
        "base_report_to_printer",
        "stock_picking_auto_print",
    ],
    "data": [
        "views/stock_picking_views.xml",
        "views/stock_picking_type_views.xml",
        "reports/shipping_label_report.xml",
    ],
}
