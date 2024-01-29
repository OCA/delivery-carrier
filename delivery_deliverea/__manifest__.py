# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Delivery Deliverea",
    "summary": "Delivery Carrier implementation for Deliverea using their API",
    "version": "16.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "FactorLibre, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery_state",
        "delivery_package_number",
    ],
    "external_dependencies": {"python": ["unidecode"]},
    "data": [
        "data/deliverea_states_data.xml",
        "data/product_packaging_data.xml",
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/deliverea_distribution_center_views.xml",
        "views/deliverea_state_mapping.xml",
        "views/delivery_carrier_views.xml",
        "views/stock_picking_views.xml",
    ],
}
