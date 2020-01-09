# Copyright 2013-2019 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models, _


_logger = logging.getLogger(__name__)


class PostlogisticsLicense(models.Model):
    _name = 'postlogistics.license'
    _description = 'PostLogistics Franking License'

    _order = 'sequence'

    name = fields.Char(string='Description',
                       translate=True,
                       required=True)
    number = fields.Char(string='Number',
                         required=True)
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='Company',
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    sequence = fields.Integer(
        string='Sequence',
        help="Gives the sequence on company to define priority on license "
             "when multiple licenses are available for the same group of "
             "service."
    )


POSTLOGISTIC_TYPES = [
    ('label_layout', 'Label Layout'),
    ('output_format', 'Output Format'),
    ('resolution', 'Output Resolution'),
    ('basic', 'Basic Service'),
    ('additional', 'Additional Service'),
    ('delivery', 'Delivery Instructions')
]


class DeliveryCarrierTemplateOption(models.Model):
    """ Set name translatable and add service group """
    _inherit = 'delivery.carrier.template.option'

    name = fields.Char(translate=True)
    postlogistics_type = fields.Selection(
        selection=POSTLOGISTIC_TYPES,
        string="PostLogistics option type",
    )
    # relation tables to manage compatiblity between basic services
    # and other services
    postlogistics_basic_service_ids = fields.Many2many(
        comodel_name='delivery.carrier.template.option',
        relation='postlogistics_compatibility_service_rel',
        column1='service_id',
        column2='basic_service_id',
        string="Basic Services",
        domain=[('postlogistics_type', '=', 'basic')],
        help="List of basic service for which this service is compatible",
    )
    postlogistics_additonial_service_ids = fields.Many2many(
        comodel_name='delivery.carrier.template.option',
        relation='postlogistics_compatibility_service_rel',
        column1='basic_service_id',
        column2='service_id',
        string="Compatible Additional Services",
        domain=[('postlogistics_type', '=', 'additional')],
    )
    postlogistics_delivery_instruction_ids = fields.Many2many(
        comodel_name='delivery.carrier.template.option',
        relation='postlogistics_compatibility_service_rel',
        column1='basic_service_id',
        column2='service_id',
        string="Compatible Delivery Instructions",
        domain=[('postlogistics_type', '=', 'delivery')],
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

    delivery_type = fields.Selection(selection_add=[('postlogistics',
                                                     'Post logistics')])
    allowed_tmpl_options_ids = fields.Many2many(
        'delivery.carrier.template.option',
        compute='_compute_allowed_options_ids',
        store=False,
    )

    @api.depends('delivery_type',
                 'available_option_ids',
                 'available_option_ids.tmpl_option_id',
                 'available_option_ids.postlogistics_type',
                 )
    def _compute_basic_service_ids(self):
        """ Search in all options for PostLogistics basic services if set """
        for carrier in self:
            if carrier.delivery_type != 'postlogistics':
                continue

            options = carrier.available_option_ids.filtered(
                lambda option: option.postlogistics_type == 'basic'
            ).mapped('tmpl_option_id')

            if not options:
                continue
            self.postlogistics_basic_service_ids = options

    @api.depends('delivery_type',
                 'postlogistics_basic_service_ids',
                 'available_option_ids',
                 'available_option_ids.postlogistics_type',
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
            if carrier.delivery_type != 'postlogistics':
                domain.append(('partner_id', '=', False))
            else:
                basic_services = carrier.postlogistics_basic_service_ids
                if basic_services:
                    related_services = option_template_obj.search(
                        [('postlogistics_basic_service_ids', 'in',
                          basic_services.ids)]
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
                    opt.tmpl_option_id.postlogistics_type
                    for opt in carrier.available_option_ids
                    if opt.postlogistics_type in single_option_types and
                    opt.mandatory]
                if selected_single_options != single_option_types:
                    services = option_template_obj.search(
                        [('postlogistics_type', 'in', single_option_types),
                         ('postlogistics_type', 'not in',
                          selected_single_options)],
                    )
                    allowed |= services
                partner = self.env.ref('delivery_carrier_label_postlogistics'
                                       '.partner_postlogistics')
                domain.append(('partner_id', '=', partner.id)),
                domain.append(('id', 'in', allowed.ids))

            carrier.allowed_tmpl_options_ids = option_template_obj.search(
                domain)

    postlogistics_license_id = fields.Many2one(
        comodel_name='postlogistics.license',
        string='PostLogistics Franking License',
    )
    postlogistics_basic_service_ids = fields.One2many(
        comodel_name='delivery.carrier.template.option',
        compute='_compute_basic_service_ids',
        string='PostLogistics Service Group',
        help="Basic Service defines the available "
             "additional options for this delivery method",
    )

    @api.multi
    def postlogistics_rate_shipment(self, order):
        self.ensure_one()
        delivery_product_price = self.product_id and self.product_id.lst_price
        if delivery_product_price:
            return {
                'success': True,
                'price': delivery_product_price,
                'error_message': False,
                'warning_message': False
            }
        else:
            return {
                'success': False,
                'price': 0.0,
                'error_message': False,
                'warning_message': _(
                    'No sales price is defined on delivery product % ' %
                    self.product_id)
            }

    @api.multi
    def postlogistics_send_shipping(self, pickings):
        return [{'exact_price': False, 'tracking_number': False}]

    @api.multi
    def postlogistics_get_tracking_link(self, picking):
        return "https://service.post.ch/EasyTrack/" \
               "submitParcelData.do?formattedParcelCodes=%s" % \
               picking.carrier_tracking_ref

    @api.multi
    def postlogistics_cancel_shipment(self, pickings):
        raise NotImplementedError()
