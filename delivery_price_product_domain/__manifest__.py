# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Price Product Domain",
    "summary": "Apply domain to product in shipping charges rules",
    "author": "Ooops, Cetmix, Odoo Community Association (OCA)",
    "maintainers": ["solo4games", "CetmixGitDrone"],
    "website": "https://github.com/OCA/delivery-carrier",
    "license": "AGPL-3",
    "category": "Delivery",
    "version": "15.0.1.0.0",
    "application": False,
    "installable": True,
    "depends": ["delivery", "delivery_price_rule_untaxed"],
    "data": ["views/delivery_price_rule_views.xml"],
}
