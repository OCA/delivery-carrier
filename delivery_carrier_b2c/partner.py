# -*- coding: utf-8 -*-
#    Author: Chafique DELLI <chafique.delli@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    use_b2c_info = fields.Boolean('Advanced address',
                                  help="Display additional information for "
                                       "home delivery (b2c)")
    door_code = fields.Char('Door Code')
    door_code2 = fields.Char('Door Code 2')
    intercom = fields.Char('Intercom', help="Informations for Intercom such as"
                           " name or number on the intercom")
