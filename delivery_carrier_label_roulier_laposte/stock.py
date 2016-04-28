# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
##############################################################################

from openerp.tools.config import config
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp

from datetime import datetime, timedelta
LAPOSTE_CARRIER_TYPE = 'laposte'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # devrait etre dans customs quelque chose
    laposte_to_country = fields.Char(
        "Country where the picking is delivered",
        help="Usefull for statistics about exports",
    )

    laposte_from_country = fields.Char(
        "Country of origin of the picking",
        help="Usefull for statistics about exports",
    )

    # a mettre dans packages ou dans picking ?
    laposte_amount = fields.Float(
        "Sum of products in the packages",
        help="Usefull for custom declarations. Currency of from_country",
        digits=dp.get_precision('Product Price')
    )

    # a mettre dans packages ou dans picking ?
    laposte_cod = fields.Float(
        "Cash on delivery",
        help="Amount in the currency of to_country",
        digits=dp.get_precision('Product Price'),
    )

    laposte_insurance = fields.Float(
        "Insurance amount",
        help="Amount in the currency of from_country",
    )

    laposte_custom_category = fields.Selection(
        selection=[
            ("1", "Gift"),
            ("2", "Samples"),
            ("3", "Commercial Goods"),
            ("4", "Documents"),
            ("5", "Other"),
            ("6", "Goods return"),
        ],
        help="Type of sending for the customs",
        default="3")  # todo : extraire ca dans roulier_international

    def _laposte_is_our(self):
        return self.carrier_id.type == LAPOSTE_CARRIER_TYPE

    def _laposte_before_call(self, package_id, request):
        def cacl_package_price(package_id):
            return sum(
                [op.product_id.list_price * op.product_qty
                    for op in package_id.get_operations()]
            )
        request['parcel']['nonMachinable'] = package_id.laposte_non_machinable
        request['service']['totalAmount'] = '%.f' % (  # truncate to string
            cacl_package_price(package_id) * 100  # totalAmount is in centimes
        )
        request['service']['transportationAmount'] = 10  # how to set this ?
        request['service']['returnTypeChoice'] = 3  # do not return to sender
        return request

    def _laposte_after_call(self, package_id, response):
        # CN23 is included in the pdf url
        return {
            'name': response['parcelNumber'],
            'url': response['url'],
            'type': 'url',
        }

    def _laposte_get_shipping_date(self, package_id):
        """Estimate shipping date."""
        self.ensure_one()

        shipping_date = self.min_date
        if self.date_done:
            shipping_date = self.date_done

        shipping_date = datetime.strptime(
            shipping_date, DEFAULT_SERVER_DATETIME_FORMAT)

        tomorrow = datetime.now() + timedelta(1)
        if shipping_date < tomorrow:
            # don't send in the past
            shipping_date = tomorrow

        return shipping_date.strftime('%Y-%m-%d')

    @api.multi
    def _laposte_get_options(self):
        """Define options for the shippment.

        Like insurance, cash on delivery...
        It should be the same for all the packages of
        the shippment.
        """
        # should be extracted from a company wide setting
        # and oversetted in a view form
        self.ensure_one()
        option = {}
        # TODO implement here
        # if self.option_ids:
        #    for opt in self.option_ids:
        #        opt_key = str(opt.tmpl_option_id['code'].lower())
        #        option[opt_key] = True
        return option

    @api.multi
    def _laposte_get_account(self):
        """Fetch a laposte login/password.

        Currently it's global for the company.
        TODO:
            * allow multiple accounts
            * store the password securely
            * inject it via ENVIRONMENT variable
        """
        self.ensure_one()
        return {
            'login': self.company_id.laposte_login,
            'password': self.company_id.laposte_password
        }

    @api.multi
    def _laposte_get_customs(self, package_id):
        """Format customs infos for each product in the package.

        The decision whether to include these infos or not is
        taken in _should_include_customs()

        Returns:
            dict.'articles' : list with qty, weight, hs_code
            int category: gift 1, sample 2, commercial 3, ...
        """
        articles = []
        for operation in package_id.get_operations():
            article = {}
            articles.append(article)
            product = operation.product_id
            # stands for harmonized_system
            hs = product.product_tmpl_id.get_hs_code_recursively()

            article['quantity'] = '%.f' % operation.product_qty
            article['weight'] = (operation.get_weight() / operation.product_qty)
            article['originCountry'] = product.origin_country_id.code
            article['description'] = hs.description
            article['hs'] = hs.hs_code
            article['value'] = product.list_price  # unit price is expected
            # todo : extraire ca dans roulier_international

        category = self.laposte_custom_category
        return {
            "articles": articles,
            "category": category,
        }

    @api.multi
    def _laposte_should_include_customs(self, package_id):
        """Choose if customs infos should be included in the WS call.

        Return bool
        """
        # Customs declaration (cn23) is needed when :
        # dest is not in UE
        # dest is attached territory (like Groenland, Canaries)
        # dest is is Outre-mer
        #
        # see https://boutique.laposte.fr/_ui/doc/formalites_douane.pdf
        # Return true when not in metropole.
        international_products = (
            'COM', 'CDS',  # outre mer
            'COLI', 'CORI',  # colissimo international
            'BOM', 'BDP', 'BOS', 'CMT',  # So Colissimo international
        )
        return self.carrier_code.upper() in international_products

    # voir pour y mettre en champ calcule ?
    @api.multi
    def _laposte_get_parcel_tracking(self):
        """Get the list of tracking numbers.

        Each package may have his own tracking number
        returns:
            list of string
        """
        self.ensure_one()
        return [pack.parcel_tracking
                for pack in self._get_packages_from_picking()
                if pack.parcel_tracking]
