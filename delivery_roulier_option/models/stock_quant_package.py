#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.delivery_roulier import implemented_by_carrier


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    @implemented_by_carrier
    def _get_cash_on_delivery(self, picking):
        pass

    @implemented_by_carrier
    def _get_customs(self, picking):
        pass

    @implemented_by_carrier
    def _get_sale_price(self, picking):
        pass

    @implemented_by_carrier
    def _should_include_customs(self, picking):
        pass

    def _roulier_get_cash_on_delivery(self, picking):
        """for 'cod' option"""
        # TODO improve to take account Sale if picking created from sale
        amount = 0
        for oper in self.get_operations():
            amount += oper.product_id.list_price * oper.product_qty
        return amount

    def _roulier_should_include_customs(self, picking):
        """Choose if custom docs should be sent.

        Really dumb implementation.
        You may improve this for your carrier.
        """
        sender = picking._get_sender(self)
        receiver = picking._get_receiver(self)
        return sender.country_id.code != receiver.country_id.code

    def _roulier_get_customs(self, picking):
        """Format customs infos for each product in the package.

        The decision whether to include these infos or not is
        taken in _should_include_customs()

        Returns:
            dict.'articles' : list with qty, weight, hs_code
            int category: gift 1, sample 2, commercial 3, ...
        """
        self.ensure_one()

        articles = []
        for operation in self.get_operations():
            article = {}
            articles.append(article)
            product = operation.product_id
            # stands for harmonized_system
            hs = product.get_hs_code_recursively()
            if not hs:
                raise UserError(
                    _(
                        "No H.S. Code on product '%s' nor on it's "
                        "product category '%s'."
                    )
                    % (product.display_name, product.categ_id.display_name)
                )

            article["quantity"] = "%.f" % (operation.qty_done or operation.product_qty)
            article["weight"] = operation.get_weight() / (
                operation.qty_done or operation.product_qty
            )
            article["originCountry"] = product.origin_country_id.code
            article["description"] = hs.description or product.name[:60]
            article["hsCode"] = hs.hs_code
            article["value"] = operation.get_unit_price_for_customs()

        category = picking.customs_category
        return {
            "articles": articles,
            "category": category,
        }

    def _roulier_get_sale_price(self, picking):
        """helper. Could be use to compute an insurance value or a value
        for customs
        """
        total = 0.0
        for operation in self.get_operations():
            total += operation.get_unit_price_for_customs() * operation.product_qty
        return total
