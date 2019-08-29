#  @author David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


MESSAGE = _(
    "Account name must be in %s as Provider field value (delivery_type)")


class CarrierAccount(models.Model):
    _inherit = 'carrier.account'

    @api.constrains("name")
    def name_constraint(self):
        values = [
            x[0] for x in
            self.env["delivery.carrier"]._fields['delivery_type'].selection
            if x[0] not in ("fixed", "base_on_rule")]
        for rec in self:
            if rec.name not in values:
                raise UserError(MESSAGE % values)
