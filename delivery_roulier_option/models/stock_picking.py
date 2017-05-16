# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from functools import wraps
import logging
from openerp import models, fields, api

_logger = logging.getLogger(__name__)


def implemented_by_carrier(func):
    """Decorator: call _carrier_prefixed method instead.

    Usage:
        @implemented_by_carrier
        def _do_something()
        def _laposte_do_something()
        def _gls_do_something()

    At runtime, picking._do_something() will try to call
    the carrier spectific method or fallback to generic _do_something

    """
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        fun_name = func.__name__
        fun = '_%s%s' % (cls.carrier_type, fun_name)
        if not hasattr(cls, fun):
            fun = '_roulier%s' % (fun_name)
            # return func(cls, *args, **kwargs)
        return getattr(cls, fun)(*args, **kwargs)
    return wrapper


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    display_insurance = fields.Boolean(
        compute='_compute_check_options',
        string="Define a condition to display/hide your custom Insurance"
               "field with a decated view")

    @implemented_by_carrier
    def _map_options(self):
        pass

    @implemented_by_carrier
    def _get_options(self, package):
        pass

    @api.multi
    @api.depends('option_ids')
    def _compute_check_options(self):
        insurance_opt = self.env.ref(
            'delivery_roulier_option.carrier_opt_tmpl_INS', False)
        for rec in self:
            if insurance_opt in [x.tmpl_option_id for x in rec.option_ids]:
                rec.display_insurance = True
            else:
                rec.display_insurance = False
                _logger.info("   >>> in _compute_check_options() %s" %
                             rec.display_insurance)

    @api.model
    def _roulier_map_options(self):
        """Customize this mapping with your own carrier.

        Like
            return {
                'FCR': 'fcr',
                'COD': 'cod',
                'INS': 'ins',
            }
        """
        return {}

    def _roulier_get_options(self, package):
        mapping_options = self._map_options()
        options = {}
        if self.option_ids:
            for opt in self.option_ids:
                opt_key = str(opt.tmpl_option_id['code'])
                if opt_key in mapping_options:
                    options[mapping_options[opt_key]] = True
                else:
                    options[opt_key] = True
        return options
