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


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    seur_service_code = fields.Selection([
        ('001', 'SEUR - 24'),
        ('003', 'SEUR - 10'),
        ('005', 'MISMO DIA'),
        ('007', 'COURIER'),
        ('009', 'SEUR 13:30'),
        ('013', 'SEUR - 72'),
        ('015', 'S-48'),
        ('017', 'MARITIMO'),
        ('019', 'NETEXPRESS'),
        ('077', 'CLASSIC'),
        ('083', 'SEUR 8:30')
    ], 'Seur Service Code')
    seur_product_code = fields.Selection([
        ('002', 'ESTANDAR'),
        ('004', 'MULTIPACK'),
        ('006', 'MULTI BOX'),
        ('018', 'FRIO'),
        ('052', 'MULTI DOC'),
        ('054', 'DOCUMENTOS'),
        ('070', 'INTERNACIONAL T'),
        ('072', 'INTERNACIONAL A'),
        ('076', 'CLASSIC')
    ], 'Seur Product Code')

    @api.model
    def _get_carrier_type_selection(self):
        """ Add SEUR carrier type """
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('seur', 'SEUR'))
        return res

    seur_config_id = fields.Many2one('seur.config', string='SEUR Config')
