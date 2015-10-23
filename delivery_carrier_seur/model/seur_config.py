##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#                  Ismael Calvo <ismael.calvo@factorlibre.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class SeurConfig(models.Model):
    _name = 'seur.config'

    def _default_company(self):
        return self.env.user.company_id

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=_default_company)
    ws_url = fields.Char('Webservice URL', required=True,
                         default="https://cit.seur.com/CIT-war/services")
    integration_code = fields.Char('Integration Code', required=True)
    accounting_code = fields.Char('Accounting Code', required=True)
    franchise_code = fields.Char('Franchise Code', required=True)
    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    file_type = fields.Selection('_get_file_type',
                                 string="File type",
                                 required=True)

    @api.model
    def _get_file_type(self):
        return [
            ('pdf', 'PDF'),
            ('txt', 'TXT')
        ]
