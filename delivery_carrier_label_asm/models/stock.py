# -*- coding: utf-8 -*-
# © 2013-2015 David BEAL <david.beal@akretion.com>
# © 2017 Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import base64

from random import randint
import requests
from base64 import decodestring

from .api import API
from .picking import *

import logging

_logger = logging.getLogger(__name__)
try:
    import pycountry
except (ImportError, IOError) as err:
    _logger.debug(err)


EXCEPT_TITLE = _("ASM Library Exception")
LABEL_TYPE = 'pdf'

test_username = '6BAB7A53-3B6D-4D5A-9450-702D2FAC0B11'


def raise_exception(message):
    raise Warning(_("%s\n%s") % (EXCEPT_TITLE, map_except_message(message)))


def map_except_message(message):
    """ Allows to map vocabulary from external library
        to Odoo vocabulary in Exception message
    """
    model_mapping = {
        'shipper_country': 'partner_id.country_id.code',
    }
    for key, val in model_mapping.items():
        message = message.replace(key, val)
    return message


class StockPicking(models.Model):
    _inherit = "stock.picking"

    asm_label = fields.Selection(
        [('PDF', 'PDF'),
         ('EPL', 'EPL'),
         ('DPL', 'DPL'),
         ('PNG', 'PNG'),
         ('JPG', 'JPG')],
        string='ASM Label')

    @api.multi
    def get_asm_label(self):
        if self.carrier_code in ['asm', 'ASM']:
            return self.asm_label
        return ''

    def generate_labels(self):
        username = self.env['ir.config_parameter'].get_param(
            'carrier_asm_customer_code')

        with Picking(username) as picking_api:
            data = {}
            for picking in self:
                type = picking.get_asm_label()
                # sender data
                data.update({
                    'remite_nombre': picking.company_id.name,
                    'remite_direccion': picking.company_id.street,
                    'remite_poblacion': picking.company_id.city,
                    'remite_provincia': picking.company_id.state_id.name,
                    'remite_pais': picking.company_id.country_id.code,
                    'remite_cp': picking.company_id.zip,
                    'etiqueta': type
                })
                # destination data
                if self.partner_id:
                    data.update({
                        'destinatario_nombre': picking.partner_id.name,
                        'destinatario_direccion': picking.partner_id.street,
                        'destinatario_poblacion': picking.partner_id.city,
                        'destinatario_pais': picking.partner_id.
                        country_id.code,
                        'destinatario_cp': picking.partner_id.zip,
                        'destinatario_observaciones': picking.note,
                        'referencia_c': randint(1000, 2000)
                    })

                reference, label, error = picking_api.create(data)
                if not error:
                    pdf = decodestring(label.encode())
                    attachment = self.env['ir.attachment'].create({
                        'name': 'ASM_Etiqueta',
                        'datas': base64.encodestring(pdf),
                        'datas_fname': 'ASM_Etiqueta.{}'.format(type),
                        'type': 'binary',
                    })
                    message_id = self.env['mail.message'].create({
                        'res_id': picking.id,
                        'model': picking._name,
                        'message_type': 'comment',
                        'attachment_ids': [(4, attachment.id)],
                        'body': 'Etiqueta ASM'
                    })
                    picking.message_ids = [(4, message_id.id)]
                    # get label with the reference number
                    data = {}
                    data.update({
                        'codigo': reference,
                        'tipo_etiqueta': type
                    })
                    label = picking_api.label(data)
                    pdf = decodestring(label.encode())
                    attachment = self.env['ir.attachment'].create({
                        'name': 'ASM_Referencia',
                        'datas': base64.encodestring(pdf),
                        'datas_fname': 'ASM_Referencia.{}'.format(type),
                        'type': 'binary',
                    })
                    message_id = self.env['mail.message'].create({
                        'res_id': picking.id,
                        'model': picking._name,
                        'message_type': 'comment',
                        'attachment_ids': [(4, attachment.id)],
                        'body': 'Referencia ASM'
                    })
                    picking.message_ids = [(4, message_id.id)]
                else:
                    raise ValidationError(error)

    @api.multi
    def action_done(self):
        self.filtered(lambda picking: picking.carrier_code == 'asm'
                      ).generate_labels()
        return super(StockPicking, self).action_done()
