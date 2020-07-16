# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery carrier label note",
    "version": "12.0.1.0.0",
    "author": "Odoo Nodriza Tech (ONT)",
    "website": "https://nodrizatech.com/",
    "category": "Delivery",
    "license": "AGPL-3",
    "depends": [
        "base_delivery_carrier_label",
        "sale_stock"
    ],
    "data": [
        "views/sale_order_view.xml",
        "views/stock_picking_view.xml",
    ],
    "installable": True
}