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
import base64
from datetime import datetime

from odoo import models, fields, api, exceptions, _
from ..json.spring_api import SpringRequest


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_spring_service_type(self):
        return [
            ('TRCK', 'Tracked'),
            ('SIGN', 'Signature'),
            ('UNTR', 'Untracked'),
        ]

    spring_service_type = fields.Selection('_get_spring_service_type', string='Spring Service')
    sub_carrier = fields.Char('Sub delivery carrier')
    sub_carrier_tracking_ref = fields.Char('Second tracking number')
    sub_carrier_service = fields.Char('Sub carrier service')
    sub_carrier_url = fields.Char('Sub carrier url')

    def _spring_shipment_request(self):
        data = {'Command':'OrderShipment'}

        warehouse_address = self.picking_type_id.warehouse_id.partner_id
        product_list = []
        package_content = None
        reference_content = None
        weigth_content = 0
        length_pack = 0
        width_pack = 0
        height_pack = 0

        sale = self.env['sale.order'].search([('name', '=', self.origin)])

        for move in self.move_lines:
            product = {
                "Description":move.product_id.name,
                "Sku":move.product_id.default_code,
                "HsCode":'',
                "OriginCountry":'',
                "PurchaseUrl":'',
                "Quantity":move.product_uom_qty,
                "Value":move.product_id.standard_price
            }
            product_list.append(product)
            package_content = ('%s %s' % (package_content, move.product_id.name)).strip()
            reference_content = '%s|%s' % ((('%sx(%s)' % (int(move.product_uom_qty), move.product_id.default_code)) if move.product_uom_qty > 1
                                            else move.product_id.default_code),
                                           reference_content)
            weigth_content = weigth_content + (move.product_id.weight * move.product_uom_qty)
            length_pack = length_pack + (move.product_id.length * move.product_uom_qty)
            if width_pack < move.product_id.width:
                width_pack = move.product_id.width
            if height_pack < move.product_id.height:
                height_pack = move.product_id.height

        # TODO: Check postal codes formats per country
        shipment_data = {
            'LabelOption':'FinalMile',
            'LabelFormat':'PDF',
            'ShipperReference':'%s-%s' % (self.name, datetime.now()),  # TODO remove datetime, it is for test only
            'DisplayId':'',
            'InvoiceNumber':'',
            'Service':self.carrier_id.code,
            'ConsignorAddress':{
                "Name":warehouse_address.name,
                "Company":warehouse_address.name,
                "AddressLine1":warehouse_address.street,
                "AddressLine2":warehouse_address.street2,
                "AddressLine3":warehouse_address.street3,
                "City":warehouse_address.city,
                "State":warehouse_address.state_id.name,
                "Zip":warehouse_address.zip,
                "Country":warehouse_address.country_id.code,
                "Phone":warehouse_address.phone,
                "Email":warehouse_address.email,
                "Vat":warehouse_address.vat,
                "Eori":''
            },
            "ConsigneeAddress":{
                "Name":self.partner_id.name,
                "Company":'',
                "AddressLine1":self.partner_id.street,
                "AddressLine2":self.partner_id.street2,
                "AddressLine3":self.partner_id.street2,
                "City":self.partner_id.city,
                "State":self.partner_id.state_id.name,
                "Zip":self.partner_id.zip,
                "Country":self.partner_id.country_id.code,
                "Phone":self.partner_id.phone,
                "Email":self.partner_id.email,
                "Vat":'',
            },
            "Weight":weigth_content or 1,
            "WeightUnit":"kg",
            "Length":length_pack or 10,
            "Width":width_pack or 10,
            "Height":height_pack or 10,
            "DimUnit":"cm",
            "Value":sale.amount_total,
            "Currency":sale.order_line.mapped('currency_id').name,
            "CustomsDuty":"DDU",
            "Description":package_content,
            "DeclarationType":"SaleOfGoods",
            "Products":product_list

        }

        data['Shipment'] = shipment_data

        return data

    @api.multi
    def _generate_spring_label(self, package_ids=None):
        self.ensure_one()
        if not self.carrier_id.spring_config_id:
            raise exceptions.Warning(_('No Spring Config defined in carrier'))
        if not self.picking_type_id.warehouse_id.partner_id:
            raise exceptions.Warning(
                _('Please define an address in the %s warehouse') % (
                    self.warehouse_id.name))

        spring_api = SpringRequest(self.carrier_id.spring_config_id)

        # Generate shipment data
        shipment_data_request = self._spring_shipment_request()
        response = spring_api.api_request(shipment_data_request)
        if response['ErrorLevel'] != 0:
            raise exceptions.Warning(response['Error'])

        ship_response = response['Shipment']

        # label_response = self._get_spring_label(spring_api, ship_response['TrackingNumber'])

        label = {
            'file':base64.b64decode(ship_response['LabelImage']),
            'file_type':'pdf',
            'name':ship_response['TrackingNumber'] + '.pdf',
            'tracking_number':ship_response['TrackingNumber'],
        }

        self.carrier_tracking_ref = ship_response['TrackingNumber']

        self.sub_carrier = ship_response['Carrier']
        self.sub_carrier_tracking_ref = ship_response['CarrierTrackingNumber']
        self.sub_carrier_service = ship_response['Service']
        self.sub_carrier_url = ship_response['CarrierTrackingUrl']

        return [label]

    @api.multi
    def _get_spring_label(self, spring_api, shipping_number):
        self.ensure_one()
        shipment = {'LabelFormat':'PDF',
                    'TrackingNumber':shipping_number}
        data = {'Command':'GetShipmentLabel', 'Shipment':shipment}
        response = spring_api.api_request(data)
        return response if response and response.get('ErrorLevel') == 0 else None

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """ Add label generation for Spring """
        self.ensure_one()
        if self.carrier_id.carrier_type == 'spring':
            return self._generate_spring_label(package_ids=package_ids)
        return super(StockPicking, self).generate_shipping_labels(
            package_ids=package_ids)
