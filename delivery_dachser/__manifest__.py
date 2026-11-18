# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Dachser",
    "summary": (
        "Delivery Carrier implementation for Dachser REST API v2: "
        "quotations, transport orders, PDF/ZPL labels, tracking and POD"
    ),
    "version": "18.0.2.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Acysos S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "delivery_package_number",
        "delivery_state",
        "stock_picking_volume",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/product_packaging_data.xml",
        "views/delivery_carrier_views.xml",
        "views/res_partner_views.xml",
        "views/stock_package_type_views.xml",
        "views/stock_picking_views.xml",
        "wizards/dachser_transfer_list_wizard_views.xml",
    ],
    "maintainers": ["victoralmau"],
}
