# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
from openerp import api, fields, models, exceptions, _

logger = logging.getLogger(__name__)


try:
    from transsmart.connection import Connection
except ImportError as error:
    logger.error(
        'Transsmart-V2 missing, transsmart integration will not work')
    raise error


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cost_center_id = fields.Many2one(
        'cost.center',
        string='Delivery Cost Center',
    )
    delivery_cost = fields.Float('Delivery Cost', readonly=True, copy=False)
    delivery_cost_currency_id = fields.Many2one('res.currency')
    # Not all carrier's support all service level time ids
    # their frontend somehow knows which carriers support what.
    # the documentation does not mention a way/field for us to know
    # and the js that operates on their end is obfuscated.
    # in any case if the user selects an invalid service_level_time_id value
    # they will get an error message back.
    service_level_time_id = fields.Many2one(
        'service.level.time',
        string='Service Level Time',
    )
    service_level_other_id = fields.Many2one(
        'service.level.other',
        string='Service Level Other',
    )
    incoterm_id = fields.Many2one(
        'stock.incoterms',
        string='Incoterm',
    )
    booking_profile_id = fields.Many2one('booking.profile', 'Booking Profile')
    send_to_transsmart = fields.Boolean(
        compute='_compute_send_to_transsmart',
        store=True,
    )
    package_type_id = fields.Many2one('product.template')

    @api.depends('company_id', 'picking_type_id')
    @api.multi
    def _compute_send_to_transsmart(self):
        for rec in self.filtered(
                lambda x: x.picking_type_id.code == 'outgoing'):
            rec.send_to_transsmart = rec._send_to_transsmart()

    @api.onchange('booking_profile_id')
    def onchange_booking_profile_id(self):
        self.update({
            'cost_center_id': self.booking_profile_id.costcenter_id.id,
            'service_level_time_id':
                self.booking_profile_id.service_level_time_id.id,
            'service_level_other_id':
                self.booking_profile_id.service_level_other_id.id,
            'incoterm_id': self.booking_profile_id.incoterms_id.id,
            'package_type_id':
                self.booking_profile_id.carrier_id.package_type_id.id
        })

    service = fields.Selection(
        [('DOCS', 'DOCS'), ('NON-DOCS', 'NON-DOCS')],
        default='NON-DOCS',
    )

    @api.multi
    def _get_invoice_name(self):
        invoice_name = ''
        if self.sale_id.name:
            invoice_name = self.env['account.invoice'].search([
                ('origin', '=', self.sale_id.name),
            ]).number
        return invoice_name

    def _transsmart_create_shipping(self):
        """
        This assembles and returns the payload to be sent to Transsmart on
        https://devdocs.transsmart.com/#_shipment_booking_only.
        """
        self.ensure_one()
        document = {
            'reference': self.name,
            'additionalReferences': [
                {'type': 'ORDER', 'value': self.sale_id.name},
                {'type': 'OTHER', 'value': self._get_invoice_name()},
                {'type': 'INVOICE', 'value': self._get_invoice_name()},
            ],
            'addresses': [
                {
                    'type': 'SEND',  # address of the sender
                    'name': self.company_id.name,
                    'addressLine1': self.company_id.street,
                    'addressLine2': self.company_id.street2,
                    'zipCode': self.company_id.zip,
                    'city': self.company_id.city,
                    'state': self.company_id.state_id.code,
                    'country': self.company_id.country_id.code,
                    'email': self.company_id.email,
                    'telNo': self.company_id.phone,
                },
                {
                    'type': 'RECV',  # address of the receiver
                    'name': self.partner_id.name,
                    'addressLine1': self.partner_id.street,
                    'addressLine2': self.partner_id.street2,
                    'zipCode': self.partner_id.zip,
                    'city': self.partner_id.city,
                    'state': self.partner_id.state_id.code,
                    'country': self.partner_id.country_id.code,
                    'contact': self.partner_id.name,
                    'telNo': self.partner_id.phone,
                    'email': self.partner_id.email,
                },
            ],
            # for now a single package that contains everything
            'packages': [{
                'measurements':
                    {
                        'length': self.package_type_id.length,
                        'width': self.package_type_id.width,
                        'height': self.package_type_id.height,
                        'weight': self.package_type_id.weight,
                    },
                'packageType': self.package_type_id._type,
                'quantity': 1,  # one package for everything
                'deliveryNoteInfo': {
                    'deliveryNoteLines': [
                        {
                            'hsCode':
                                line.product_id.hs_code_id.hs_code,
                            'hsCodeDescription':
                                line.product_id.hs_code_id.description,
                            'description': line.name,
                            'price': line.product_id.lst_price,
                            'currency': self.sale_id.currency_id.name,
                            'quantity': line.product_uom_qty,
                            'countryOrigin':
                                line.product_id.origin_country_id.code,
                            'articleId': self.product_id.default_code,
                            'articleName': self.product_id.name,
                        } for line in self.move_lines],
                    }
                }
            ],
            'carrier': self.booking_profile_id.carrier_id.code,
            'value': self.sale_id.amount_total,
            'valueCurrency': self.sale_id.currency_id.name,
            'service': self.service,
            'serviceLevelTime': self.service_level_time_id.code,
            'serviceLevelOther': self.service_level_other_id.code,
            'incoterms': self.incoterm_id.code,
            'costCenter': self.cost_center_id.code,
            'pickupDate': fields.Datetime.from_string(
                self.min_date).date().isoformat(),
        }
        return [document]

    def _false_to_empty_string(self, document):
        """
        Apparently, when we sent False to transsmart, it is not handled
        properly and we get a BAD_REQUEST.
        So what this function does is replace every False value with an empty
        string `''`.
        """
        if isinstance(document, dict):
            for key, value in document.iteritems():
                if isinstance(value, dict) or isinstance(value, list):
                    self._false_to_empty_string(value)
                else:
                    if value is False:
                        document[key] = ''
        elif isinstance(document, list):
            for index, value in enumerate(document):
                if isinstance(value, dict) or isinstance(value, list):
                    self._false_to_empty_string(value)
                else:
                    if value is False:
                        document[index] = ''
        return document

    def _validate_create_booking_document(self, document):
        document = document[0]
        REQUIRED_FIELDS = [
            'reference',
            'service',
            'serviceLevelTime',
            'pickupDate',
            ]
        REQUIRED_PACKAGE_FIELDS = [
            'quantity',
            ]
        for field in REQUIRED_FIELDS:
            if not document.get(field):
                raise exceptions.ValidationError(_(
                    "Field %s on %s needs to have a value.") %
                    (field, self.name))
        for address in document.get('addresses'):
            for key in address.keys():
                if not address[key] and key not in ['addressLine2', 'state']:
                    raise exceptions.ValidationError(_(
                        "Field %s on address on %s needs to have a value.") %
                        (key, self.name))
        for package in document.get('packages'):
            for key in package.get('measurements').keys():
                if package.get('measurements')[key] is None:
                    raise exceptions.ValidationError(_(
                        "Make sure that Package Type is set on %s "
                        "or on the carrier "
                        "and its dimensions length, width, height and weight "
                        "are filled.") % (self.name))
            for field in REQUIRED_PACKAGE_FIELDS:
                if not package.get(field):
                    raise exceptions.ValidationError(_(
                        "Make sure that %s field of the Package Type %s has a "
                        "value.") % (
                            field,
                            self.package_type_id.name,
                        )
                    )

    @api.multi
    def action_create_transsmart_document(self):
        """
        This creates the stock picking on Transsmart and sets some fields on
        the picking locally.
        https://devdocs.transsmart.com/#_shipment_booking_only
        """
        ir_config_parameter = self.env['ir.config_parameter']
        account_code = ir_config_parameter.get_param('transsmart_account_code')
        for rec in self:
            document = rec._false_to_empty_string(
                rec._transsmart_create_shipping())
            rec._validate_create_booking_document(document)
            connection = rec._get_transsmart_connection()
            response = connection.Shipment.book(
                account_code,
                'BOOK',
                document)
            if not response.ok:
                raise exceptions.ValidationError(_(
                    response.json()))
            response_json = response.json()[0]  # unpack
            data = {
                'delivery_cost': response_json['price'],
                'carrier_tracking_ref': response_json['trackingUrl'],
            }
            rec.write(data)

    def _send_to_transsmart(self):
        """
        Not all stock pickings can/should be sent to Transsmart.
        Figure this out here.
        """
        return self.company_id.transsmart_enabled \
            and self.picking_type_id.code == 'outgoing' \
            and self.booking_profile_id.carrier_id.partner_id.code

    def _get_transsmart_connection(self):
        """
        Return an connection object after authenticating with transsmart.
        """
        ir_config_parameter = self.env['ir.config_parameter']
        username = ir_config_parameter.get_param('transsmart_username')
        password = ir_config_parameter.get_param('transsmart_password')
        demo = ir_config_parameter.get_param('transsmart_demo')
        return Connection().connect(username, password, demo)

    def _validate_get_rates_document(self, document):
        document = document[0]
        if not document.get('reference'):
            raise exceptions.ValidationError(_(
                "Reference field needs to be filled."))
        measurements = document.get('packages')[0].get('measurements')
        for key in measurements.keys():
            if not measurements[key]:
                raise exceptions.ValidationError(_(
                    "Make sure that the Package Type along with its fields "
                    "length, width, height and weight are set."))
        packageType = document.get('packages')[0].get('packageType')
        quantity = document.get('packages')[0].get('quantity')
        pickupDate = document.get('pickupDate')
        if not packageType or not quantity or not pickupDate:
            raise exceptions.ValidationError(_(
                "Package Type field on the Package Type must be filled. "
                "Sum of quantity of the product lines must not be zero. "
                "Pickup date must be filled."))
        for address in document.get('addresses'):
            for key in address.keys():
                if not address[key] and key != 'addressLine2':
                    raise exceptions.ValidationError(_(
                        "Field %s in the receiving and sending addresses must "
                        "be filled.") % (key))

    @api.multi
    def transsmart_get_rates(self):
        """
        Get rates/offers from transsmart for the current picking and set some
        values locally.
        Attention: Only the lowest rate is saved.
        https://devdocs.transsmart.com/#_calculating_rates
        """
        ir_config_parameter = self.env['ir.config_parameter']
        account_code = ir_config_parameter.get_param('transsmart_account_code')
        for rec in self:
            connection = rec._get_transsmart_connection()
            document = rec._false_to_empty_string(
                rec._transsmart_create_shipping())
            self._validate_get_rates_document(document)
            response = connection.Rate.calculate(
                account_code,
                document)
            if not response.ok:
                raise exceptions.ValidationError(_(
                    response.json()))
            rate_obj = sorted(
                response.json()[0]['rates'],
                key=lambda x: x['price'])[0]
            rec.write({
                'delivery_cost': rate_obj['price'],
                'delivery_cost_currency_id': self.env['res.currency'].search(
                    [('name', '=', rate_obj['currency'])]).id})

    @api.model
    def create(self, vals):
        """
        When a stock picking is created *and* can be sent to transsmart, get
        the rates.
        """
        result = super(StockPicking, self).create(vals)
        if result._send_to_transsmart():
            result.transsmart_get_rates()
        return result
