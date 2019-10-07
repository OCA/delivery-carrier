# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#                  Hugo Santos <hugo.santos@factorlibre.com>
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
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_correos_service_type(self):
        return [
            ('1', 'Ordinario'),
            ('2', 'Certificado'),
            ('3', 'Urgente'),
            ('4', 'Paquetería'),
        ]

    correos_service_type = fields.Selection('_get_correos_service_type', string='Correos Service')

    @api.multi
    def _correos_etiqueta_envio_request(self, correos_api, shipping_number):
        self.ensure_one()

        return

    @api.multi
    def _generate_correos_label(self, package_ids=None):
        self.ensure_one()
        return

    @api.multi
    def _get_correos_label_from_url(self, shipping_number):
        self.ensure_one()
        return

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """ Add label generation for Correos """
        self.ensure_one()
        if self.carrier_id.carrier_type == 'correos':
            return self._generate_correos_label(package_ids=package_ids)
        return super(StockPicking, self).generate_shipping_labels(
            package_ids=package_ids)
