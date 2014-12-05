# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Sébastien BEAU <sebastien.beau@akretion.com>
#    Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#    Copyright 2014 Camptocamp SA
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


class DeliveryCarrierTemplateOption(models.Model):
    """ Available options for a carrier (partner) """
    _name = 'delivery.carrier.template.option'
    _description = 'Delivery carrier template option'

    partner_id = fields.Many2one(comodel_name='res.partner',
                                 string='Partner Carrier')
    name = fields.Char(readonly=True)
    code = fields.Char(readonly=True)
    description = fields.Char(
        readonly=True,
        help="Allow to define a more complete description "
             "than in the name field."
    )


class DeliveryCarrierOption(models.Model):
    """ Option selected for a carrier method

    Those options define the list of available pre-added and available
    to be added on delivery orders

    """
    _name = 'delivery.carrier.option'
    _description = 'Delivery carrier option'
    _inherits = {'delivery.carrier.template.option': 'tmpl_option_id'}

    mandatory = fields.Boolean(
        help="If checked, this option is necessarily applied "
             "to the delivery order"
    )
    by_default = fields.Boolean(
        string='Applied by Default',
        help="By check, user can choose to apply this option "
             "to each Delivery Order\n using this delivery method"
    )
    tmpl_option_id = fields.Many2one(
        comodel_name='delivery.carrier.template.option',
        string='Option',
        required=True,
        ondelete="cascade",
    )
    carrier_id = fields.Many2one(comodel_name='delivery.carrier',
                                 string='Carrier')
    readonly_flag = fields.Boolean(
        string='Readonly Flag',
        help="When True, help to prevent the user to modify some fields "
             "option (if attribute is defined in the view)"
    )


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def _get_carrier_type_selection(self):
        """ To inherit to add carrier type """
        return []

    type = fields.Selection(
        selection='_get_carrier_type_selection',
        string='Type',
        help="Carrier type (combines several delivery methods)",
    )
    code = fields.Char(
        help="Delivery Method Code (according to carrier)",
    )
    description = fields.Text()
    available_option_ids = fields.One2many(
        comodel_name='delivery.carrier.option',
        inverse_name='carrier_id',
        string='Option',
    )

    @api.multi
    def default_options(self):
        """ Returns default and available options for a carrier """
        options = self.env['delivery.carrier.option'].browse()
        for available_option in self.available_option_ids:
            if (available_option.mandatory or available_option.by_default):
                options |= available_option
        return options
