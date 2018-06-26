# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    SEUR_SERVICES = [
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
    ]
    SEUR_PRODUCTS = [
        ('002', 'ESTANDAR'),
        ('004', 'MULTIPACK'),
        ('006', 'MULTI BOX'),
        ('018', 'FRIO'),
        ('052', 'MULTI DOC'),
        ('054', 'DOCUMENTOS'),
        ('070', 'INTERNACIONAL T'),
        ('072', 'INTERNACIONAL A'),
        ('076', 'CLASSIC'),
        ('118', 'VINO')

    ]

    seur_service_code = fields.Selection(SEUR_SERVICES)
    seur_product_code = fields.Selection(SEUR_PRODUCTS)

    @api.model
    def _get_carrier_type_selection(self):
        """ Add SEUR carrier type """
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('seur', 'SEUR'))
        return res

    seur_config_id = fields.Many2one('seur.config', string='SEUR Config')
