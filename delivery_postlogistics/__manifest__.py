# © 2013-2016 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "PostLogistics Shipping - “Barcode” web service",
    "summary": "Print PostLogistics shipping labels using the Barcode web service",
    "version": "16.0.1.0.7",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainer": "Camptocamp",
    "license": "AGPL-3",
    "category": "Delivery",
    "complexity": "normal",
    "depends": ["delivery", "mail", "base", "stock"],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "security/ir.model.access.csv",
        "data/partner.xml",
        "data/product.xml",
        "data/delivery.xml",
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
}
