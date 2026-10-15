#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Carrier FedEx (REST API)",
    "summary": """
    Generate FedEx shipping labels through the FedEx REST APIs,
    based on the Roulier framework.
    """,
    "category": "Warehouse",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "application": False,
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Emilie SOUTIRAS, Groupe Voltaire, Odoo Community Association (OCA)",
    "maintainers": ["emiliesoutiras"],
    "depends": [
        "delivery_roulier",
        "product_harmonized_system",
    ],
    "data": [
        "views/carrier_account_views.xml",
        "data/product_product.xml",
        "data/delivery_carrier.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
