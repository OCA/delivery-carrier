import logging
import psycopg2

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WithdrawalPoints(models.Model):
    _name = "delivery.closing.period"
    _description = "Delivery Closing Period"
    _order = 'sequence, closing_id, id'

    sequence = fields.Integer(string='Sequence', default=10)
    closing_id = fields.Many2one('delivery.carrier', string='Closing reference', required=True, ondelete='cascade',
                                 index=True, copy=False)
    name = fields.Char(string='Name', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.date_from:
            self.date_to = self.date_from.replace(day=1) + relativedelta(months=1, days=-1)
