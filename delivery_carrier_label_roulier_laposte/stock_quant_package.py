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

from openerp import models, fields


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    # TODO: put this in base_delivery
    laposte_non_machinable = fields.Boolean(
        "Non Machinable",
        help="True if size of package is not standard (according to carrier)",
        default=False,
    )
