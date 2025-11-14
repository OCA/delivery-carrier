# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Carrier Geodis (fr)",
    "version": "16.0.1.1.1",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Generate Label for Geodis logistic",
    "maintainers": ["florian-dacosta"],
    "category": "Warehouse",
    "depends": [
        "delivery_roulier",
        "delivery_carrier_agency",
        "delivery_carrier_deposit",
        "delivery_roulier_option",
        "partner_address_split",
        "l10n_fr_siret",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "data/product.xml",
        "data/delivery.xml",
        "data/sequence_geodis.xml",
        "views/carrier_account_views.xml",
        "views/delivery_carrier_agency_views.xml",
    ],
    "demo": [],
    "installable": True,
    "license": "AGPL-3",
}
