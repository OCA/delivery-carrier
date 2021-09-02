# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from ..quickpac.helpers import get_language

QUICKPAC_TYPES = [
    ('label_layout', 'Label Layout'),
    ('output_format', 'Output Format'),
    ('resolution', 'Output Resolution'),
    ('basic', 'Basic Service'),
    ('additional', 'Additional Service'),
    ('delivery', 'Delivery Instructions'),
]


class DeliveryCarrierTemplateOption(models.Model):
    """ Set name translatable and add service group """

    _inherit = 'delivery.carrier.template.option'

    name = fields.Char(translate=True)
    quickpac_type = fields.Selection(
        selection=QUICKPAC_TYPES, string="Quickpac option type"
    )
    # relation tables to manage compatiblity between basic services
    # and other services
    quickpac_basic_service_ids = fields.Many2many(
        comodel_name='delivery.carrier.template.option',
        relation='quickpac_compatibility_service_rel',
        column1='service_id',
        column2='basic_service_id',
        string="Basic Services",
        domain=[('quickpac_type', '=', 'basic')],
        help="List of basic service for which this service is compatible",
    )
    quickpac_additonial_service_ids = fields.Many2many(
        comodel_name='delivery.carrier.template.option',
        relation='quickpac_compatibility_service_rel',
        column1='basic_service_id',
        column2='service_id',
        string="Compatible Additional Services",
        domain=[('quickpac_type', '=', 'additional')],
    )
    quickpac_delivery_instruction_ids = fields.Many2many(
        comodel_name='delivery.carrier.template.option',
        relation='quickpac_compatibility_service_rel',
        column1='basic_service_id',
        column2='service_id',
        string="Compatible Delivery Instructions",
        domain=[('quickpac_type', '=', 'delivery')],
    )


class DeliveryCarrierOption(models.Model):
    """ Set name translatable and add service group """

    _inherit = 'delivery.carrier.option'

    name = fields.Char(translate=True)

    allowed_tmpl_options_ids = fields.Many2many(
        'delivery.carrier.template.option',
        compute='_compute_allowed_tmpl_options_ids',
        store=False,
    )

    @api.depends('carrier_id.allowed_tmpl_options_ids')
    def _compute_allowed_tmpl_options_ids(self):
        """ Gets the available template options from related delivery.carrier
            (be it from cache or context)."""
        for option in self:
            defaults = self.env.context.get('default_allowed_tmpl_options_ids')
            option.allowed_tmpl_options_ids = (
                option.carrier_id.allowed_tmpl_options_ids or defaults or False
            )


class DeliveryCarrier(models.Model):
    """ Add service group """

    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('quickpac', 'Quickpac')])
    quickpac_basic_service_ids = fields.One2many(
        comodel_name='delivery.carrier.template.option',
        compute='_compute_basic_service_ids',
        string='Quickpac Service Group',
        help="Basic Service defines the available "
        "additional options for this delivery method",
    )
    allowed_tmpl_options_ids = fields.Many2many(
        'delivery.carrier.template.option',
        compute='_compute_allowed_options_ids',
        store=False,
    )

    @api.depends(
        'delivery_type',
        'available_option_ids',
        'available_option_ids.tmpl_option_id',
        'available_option_ids.quickpac_type',
    )
    def _compute_basic_service_ids(self):
        """ Search in all options for PostLogistics basic services if set """
        for carrier in self:
            if carrier.delivery_type != 'quickpac':
                continue

            options = carrier.available_option_ids.filtered(
                lambda option: option.quickpac_type == 'basic'
            ).mapped('tmpl_option_id')

            if not options:
                continue
            self.quickpac_basic_service_ids = options

    @api.depends(
        'delivery_type',
        'quickpac_basic_service_ids',
        'available_option_ids',
        'available_option_ids.quickpac_type',
    )
    def _compute_allowed_options_ids(self):
        """ Compute allowed delivery.carrier.option.

        We do this to ensure the user first select a basic service. And
        then he adds additional services.
        """
        option_template_obj = self.env['delivery.carrier.template.option']

        for carrier in self:
            allowed = option_template_obj.browse()
            domain = []
            if carrier.delivery_type != 'quickpac':
                domain.append(('partner_id', '=', False))
            else:
                basic_services = carrier.quickpac_basic_service_ids
                if basic_services:
                    related_services = option_template_obj.search(
                        [
                            (
                                'quickpac_basic_service_ids',
                                'in',
                                basic_services.ids,
                            )
                        ]
                    )
                    allowed |= related_services

                # Allows to set multiple optional single option in order to
                # let the user select them
                single_option_types = [
                    'label_layout',
                    'output_format',
                    'resolution',
                ]
                selected_single_options = [
                    opt.tmpl_option_id.quickpac_type
                    for opt in carrier.available_option_ids
                    if opt.quickpac_type in single_option_types
                    and opt.mandatory
                ]
                if selected_single_options != single_option_types:
                    services = option_template_obj.search(
                        [
                            ('quickpac_type', 'in', single_option_types),
                            (
                                'quickpac_type',
                                'not in',
                                selected_single_options,
                            ),
                        ]
                    )
                    allowed |= services
                partner = self.env.ref(
                    'delivery_carrier_label_quickpac.partner_quickpac'
                )
                domain.append(('partner_id', '=', partner.id)),
                domain.append(('id', 'in', allowed.ids))

            carrier.allowed_tmpl_options_ids = option_template_obj.search(
                domain
            )

    @api.multi
    def quickpac_send_shipping(self, pickings):
        return [{'exact_price': False, 'tracking_number': False}]

    @api.model
    def quickpac_get_tracking_link(self, picking):
        tracking_url = picking.company_id.quickpac_tracking_url
        return tracking_url.format(
            lang=get_language(picking.partner_id.lang),
            number=picking.carrier_tracking_ref
        )

    @api.multi
    def quickpac_cancel_shipment(self, pickings):
        raise NotImplementedError()
