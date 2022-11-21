# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Routific Connector",
    "summary": "Connector for Routific Platform",
    "version": "15.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Inventory",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "maintainers": ["CarlosRoca13"],
    "depends": ["stock", "phone_validation"],
    "external_dependencies": {"python": ["lxml", "email_validator"]},
    "data": [
        "data/sequence.xml",
        "security/ir.model.access.csv",
        "views/product_attribute_views.xml",
        "views/routific_config_views.xml",
        "views/routific_driver_views.xml",
        "views/routific_project_views.xml",
        "views/res_partner_view.xml",
        "wizards/routific_project_creator_view.xml",
        "views/routific_project_driver_view.xml",
        "views/stock_picking_views.xml",
    ],
}
