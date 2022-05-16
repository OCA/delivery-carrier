# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery TNT OCA",
    "summary": "Integrate TNT webservice",
    "version": "14.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "delivery",
        "delivery_package_number",
        "delivery_state",
        "product_dimension",
        "base_sparse_field",
    ],
    "external_dependencies": {"python": ["dicttoxml", "xmltodict"]},
    "data": [
        "views/delivery_carrier_view.xml",
        "report/picking_templates.xml",
        "report/stock_report_views.xml",
    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
