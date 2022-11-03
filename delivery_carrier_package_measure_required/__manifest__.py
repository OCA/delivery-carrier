{
    "name": "Delivery Carrier Package Measure Required",
    "summary": """
    Allow the configuration of which package measurements are required
    on a delivery carrier basis.
    """,
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "depends": [
        "stock",
        "delivery",
        # OCA/stock-logistics-workflow
        "stock_quant_package_dimension",
    ],
    "data": [
        "views/product_packaging.xml",
        "wizard/choose_delivery_package.xml",
    ],
    "installable": True,
}
