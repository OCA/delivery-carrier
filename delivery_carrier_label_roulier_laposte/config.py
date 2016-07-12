# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#          Yannick VAUCHER, Camptocamp SA
#
##############################################################################

from openerp import models, fields
from openerp import api

# TODO move to new api
# seems there is a bug with related field in new api (at least for transient)


class LaposteConfigSettings(models.TransientModel):
    _name = 'laposte.config.settings'
    _inherit = 'res.config.settings'

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=_default_company)
    laposte_login = fields.Char(related='company_id.laposte_login')
    laposte_password = fields.Char(related='company_id.laposte_password')
    laposte_support_city = fields.Char(
        related='company_id.laposte_support_city')
    laposte_support_city_code = fields.Char(
        related='company_id.laposte_support_city_code')

    @api.onchange('company_id')
    def onchange_company_id(self):

        if not self.company_id:
            # what's the point of this ?
            return
        company = self.company_id
        self.laposte_login = company.laposte_login
        self.laposte_password = company.laposte_password
        self.laposte_support_city = company.laposte_support_city
        self.laposte_support_city_code = company.laposte_support_city_code

    def button_send_image_to_printer(self, cr, uid, ids, context=None):
        """ Implement your own method according to printing solution
        """
        return LaposteConfigSettings().get_image_data()
