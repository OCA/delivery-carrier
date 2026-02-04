# © 2013 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "PostLogistics Shipping - “Barcode” web service",
    "summary": "Print PostLogistics shipping labels using the Barcode web service",
    "version": "18.0.1.3.1",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainer": "Camptocamp",
    "license": "AGPL-3",
    "category": "Delivery",
    "complexity": "normal",
    "depends": [
        "stock_delivery",
        "delivery_carrier_info",
        "delivery_carrier_option",
        "delivery_carrier_shipping_label",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "security/ir.model.access.csv",
        "data/partner.xml",
        "data/product.xml",
        "data/delivery.xml",
        "data/package_type.xml",
        "views/delivery.xml",
        "views/stock_package_type_view.xml",
        "views/stock_quant_package_view.xml",
        "views/postlogistics_license.xml",
        "views/res_partner_view.xml",
        "views/stock.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "external_dependencies": {
        "python": [
            "openupgradelib",
        ],
    },
}
