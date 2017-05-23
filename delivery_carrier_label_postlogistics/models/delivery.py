# -*- coding: utf-8 -*-
# Copyright 2013-2017 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree
from odoo import api, fields, models


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


class PostlogisticsServiceGroup(models.Model):
    _name = 'postlogistics.service.group'
    _description = 'PostLogistics Service Group'

    name = fields.Char(string='Description', translate=True, required=True)
    group_extid = fields.Integer(string='Group ID', required=True)
    postlogistics_license_ids = fields.Many2many(
        comodel_name='postlogistics.license',
        relation='postlogistics_license_service_groups_rel',
        column1='license_id',
        column2='group_id',
        string='PostLogistics Franking License')

    _sql_constraints = [
        ('group_extid_uniq', 'unique(group_extid)',
         "A service group ID must be unique.")
    ]


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
    postlogistics_service_group_id = fields.Many2one(
        comodel_name='postlogistics.service.group',
        string='PostLogistics Service Group',
    )
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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        _super = super(DeliveryCarrierOption, self)
        result = _super.fields_view_get(view_id=view_id,
                                        view_type=view_type,
                                        toolbar=toolbar, submenu=submenu)
        default_carrier_id = self.env.context.get('default_carrier_id')
        if default_carrier_id:
            carrier = self.env['delivery.carrier'].browse(default_carrier_id)
            if carrier.is_postlogistics():
                arch = result['arch']
                doc = etree.fromstring(arch)
                for node in doc.xpath("//field[@name='tmpl_option_id']"):
                    node.set(
                        'domain',
                        "[('product_id', '=', %s), "
                        " ('id', 'in', parent.allowed_option_ids[0][2])]" %
                        carrier.product_id.id
                    )
                result['arch'] = etree.tostring(doc)
        return result


class DeliveryCarrier(models.Model):
    """ Add service group """
    _inherit = 'delivery.carrier'

    @api.multi
    def is_postlogistics(self):
        self.ensure_one()
        xmlid = ('delivery_carrier_label_postlogistics'
                 '.product_postlogistics_service')
        postlogistics_delivery = self.env.ref(xmlid)
        return self.product_id == postlogistics_delivery

    @api.model
    def _get_carrier_type_selection(self):
        """ Add postlogistics carrier type """
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('postlogistics', 'Postlogistics'))
        return res

    @api.depends('product_id',
                 'available_option_ids',
                 'available_option_ids.tmpl_option_id',
                 'available_option_ids.postlogistics_type',
                 )
    def _compute_basic_service_ids(self):
        """ Search in all options for PostLogistics basic services if set """
        for carrier in self:
            if not carrier.is_postlogistics():
                continue

            options = carrier.available_option_ids.filtered(
                lambda option: option.postlogistics_type == 'basic'
            ).mapped('tmpl_option_id')

            if not options:
                continue
            self.postlogistics_basic_service_ids = options

    @api.depends('product_id',
                 'postlogistics_service_group_id',
                 'postlogistics_basic_service_ids',
                 'postlogistics_basic_service_ids',
                 'available_option_ids',
                 'available_option_ids.postlogistics_type',
                 )
    def _compute_allowed_option_ids(self):
        """ Return a list of possible options

        A domain would be too complicated.

        We do this to ensure the user first select a basic service. And
        then he adds additional services.

        """
        option_template_obj = self.env['delivery.carrier.template.option']

        for carrier in self:
            allowed = option_template_obj.browse()
            if not carrier.is_postlogistics():
                continue

            service_group = carrier.postlogistics_service_group_id
            if service_group:
                basic_services = carrier.postlogistics_basic_service_ids
                services = option_template_obj.search(
                    [('postlogistics_service_group_id', '=', service_group.id)]
                )
                allowed |= services
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
            carrier.allowed_option_ids = allowed

    postlogistics_license_id = fields.Many2one(
        comodel_name='postlogistics.license',
        string='PostLogistics Franking License',
    )
    postlogistics_service_group_id = fields.Many2one(
        comodel_name='postlogistics.service.group',
        string='PostLogistics Service Group',
        help="Service group defines the available options for "
             "this delivery method.",
    )
    postlogistics_basic_service_ids = fields.One2many(
        comodel_name='delivery.carrier.template.option',
        compute='_compute_basic_service_ids',
        string='PostLogistics Service Group',
        help="Basic Service defines the available "
             "additional options for this delivery method",
    )
    allowed_option_ids = fields.Many2many(
        comodel_name='delivery.carrier.template.option',
        compute='_compute_allowed_option_ids',
        string='Allowed options',
        help="Compute allowed options according to selected options.",
    )
