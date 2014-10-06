# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm  # fields
from openerp.tools.translate import _
from .report.label import Gls, InvalidDataForMako
from .report.label_helper import (
    #InvalidSequence,
    InvalidMissingField,
    InvalidType,)
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import os


EXCEPTION_MESSAGE_TITLE = "GLS Library Error"


def get_rescue_template():
    zpl_file = 'label_uniship.mako'
    return os.path.join(
        os.path.dirname(__file__),
        'report',
        zpl_file)


class StockPicking(orm.Model):
    _inherit = "stock.picking"

    def action_done(self, cr, uid, ids, context=None):
        """
        :return: see original method
        """
        if context is None:
            context = {}
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.carrier_type == 'gls':
                self.generate_labels(
                    cr, uid, [picking.id], context=context)
        return super(StockPicking, self).action_done(
            cr, uid, ids, context=context)

    def _prepare_address_info(self, cr, uid, picking, context=None):
        address = {}
        res = self.pool['res.partner']._get_split_address(
            cr, uid, picking.partner_id, 3, 35, context=context)
        address['street'], address['street2'], address['street3'] = res
        address.update({
            "consignee_name": picking.partner_id.name or picking.partner_id.name,
            "zip": picking.partner_id.zip,
            "city": picking.partner_id.city,
            "consignee_phone": picking.partner_id.phone,
            "consignee_mobile": picking.partner_id.mobile,
            "consignee_email": picking.partner_id.email,
            "country_code": picking.partner_id.country_id.code,
            # useful uniship label only
            "country_norme3166": picking.partner_id.country_id.gls_code,
        })
        return address

    def _prepare_sender_info(self, cr, uid, pick, context=None):
        partner = self.pool['stock.picking.out']._get_label_sender_address(
            cr, uid, pick, context=context)
        sender = {'customer_id': pick.company_id.gls_customer_code,
                  'contact_id': pick.company_id.gls_contact_id,
                  'outbound_depot': pick.company_id.gls_warehouse_code}
        if partner.country_id:
            sender['country'] = partner.country_id.name
        sender.update({
            'shipper_street': partner.street,
            'shipper_street2': partner.street1,
            'shipper_name': partner.name,
            'shipper_country': partner.country_id.code,
            'shipper_zip': partner.zip,
            'shipper_city': partner.city,
            })
        return sender

    def _prepare_delivery_info(self, cr, uid, picking, context=None):
        shipping_date = picking.min_date
        if picking.date_done:
            shipping_date = picking.date_done
        delivery = {}
        delivery.update({
            "contact": picking.company_id.name,
            'consignee_ref': picking.name,
            'additional_ref_1': '',
            'additional_ref_2': picking.name,
            'shipping_date': datetime.strptime(shipping_date,
                                DEFAULT_SERVER_DATETIME_FORMAT).strftime('%Y%m%d'),
            #'commentary': picking.note,
            'parcel_total_number': picking.number_of_packages,
            'custom_sequence': picking.carrier_sequence,
            })
        return delivery

    def _prepare_pack_info(self, cr, uid, tracking, pack_number, weight,
                                                                context=None):
        pack = {}
        pack.update({
            'parcel_number_label': pack_number,
            'parcel_number_barcode': pack_number,
            })
        if weight:
            pack.update({
                'weight': "{0:05.2f}".format(weight),
                })
        else:
            pack.update({
                'weight': "{0:05.2f}".format(tracking.weight),
                })
        return pack

    #def create_shipping_label(self, cr, uid, ids, context=None):
    #    for picking in self.browse(cr, uid, ids, context=context):
    #        if picking.carrier_type == 'gls':
    #            picking.create_shipping_label_for_gls(picking, context=context)
    #    return super(StockPicking, self).create_shipping_label(cr, uid, ids,
    #                                                           context=context)

    def _get_tracking_ids(self, cr, uid, picking, context=None):
            # get all the trackings of the picking
            # no tracking_id will return a False, meaning that
            # a label is needed for the picking
            return sorted(set(
                line.tracking_id.id or False
                for line in picking.move_lines
            ))

    def generate_shipping_labels(
            self, cr, uid, ids, tracking_ids=None, context=None):
        if isinstance(ids, (long, int)):
            ids = [ids]
        assert len(ids) == 1
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking.carrier_type == 'gls':
            #self.get_carrier_sequence(
            #    cr, uid, ids, 'stock.picking_gls', context=context)
            sender = self._prepare_sender_info(cr, uid, picking, context=context)
            #gls has a rescue label without webservice required
            #if webservice is down
            #(rescue label is also used for international carrier)
            self.label = get_rescue_template()
            test = False
            if picking.company_id.gls_test:
                test = True
            try:
                Gls_label = Gls(sender, picking.carrier_code, test_plateform=test)
            except InvalidMissingField as e:
                raise orm.except_orm(EXCEPTION_MESSAGE_TITLE, e.message)
            except Exception as e:
                raise orm.except_orm(EXCEPTION_MESSAGE_TITLE, e.message)
            pack_number = 0
            tracking_ids = self._get_tracking_ids(cr, uid, picking, context=context)
            if picking.tracking_ids:
                for tracking in picking.tracking_ids:
                    pack_number += 1
                    pack = self._prepare_pack_info(
                        cr, uid, tracking, pack_number, None, context=context)
                    self._generate_gls_label(
                        cr, uid, Gls_label, picking, pack, context=None)
            else:
                pack = self._prepare_pack_info(
                    cr, uid, None, 1, picking.weight, context=context)
                return self._generate_gls_label(
                    cr, uid, Gls_label, picking, pack, context=None)
        return super(StockPicking, self).generate_shipping_labels(
            cr, uid, ids, tracking_ids=tracking_ids, context=context)

    def _generate_gls_label(self, cr, uid, label_obj, picking, pack, context=None):
        address = self._prepare_address_infos(cr, uid, picking, context=context)
        delivery = self._prepare_delivery_infos(
            cr, uid, picking, context=context)
        try:
            result = label_obj.get_label(self.label, delivery, address, pack)
        except InvalidMissingField, e:
            raise orm.except_orm(EXCEPTION_MESSAGE_TITLE, e.message)
        except InvalidDataForMako, e:
            raise orm.except_orm(EXCEPTION_MESSAGE_TITLE, e.message)
        except InvalidType, e:
            raise orm.except_orm(EXCEPTION_MESSAGE_TITLE, e.message)
        #except Exception, e:
            #raise orm.except_orm(EXCEPTION_MESSAGE_TITLE, e.message)
        #TODO change label_code
        label_value = self.get_carrier_label_data(cr, uid, result['content'],
                    file_name=result['filename'], label_code='label_100x150',
                                                output='epl', context=context)
        picking.write({
            'shipping_label_ids': [(0, 0, label_value)],
            'carrier_tracking_ref': result['carrier_tracking_ref'],
            },
            context=context)
        #picking.write({
        #    #'carrier_tracking_ref': result['carrier_tracking_ref'],
        #    'shipping_label_ids': [(0, 0, label_value)],
        #    },
        #    context=context)
        return True


class StockPickingOut(orm.Model):
    _inherit = 'stock.picking.out'

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({
            'carrier_tracking_ref': None,
        })
        return super(StockPickingOut, self).copy(
            cr, uid, id, default, context=context)

    def get_shipping_cost(self, cr, uid, ids, context=None):
        return 0


class StockPickingIn(orm.Model):
    _inherit = 'stock.picking.in'

    def action_generate_carrier_label(self, cr, uid, ids, context=None):
        raise orm.except_orm(
            "Return label",
            "Return Label is not implemented for "
            "GLS Carrier \n"
            "For service proposal, contact http://www.akretion.com")


class ShippingLabel(orm.Model):
    _inherit = 'shipping.label'

    def _get_file_type_selection(self, cr, uid, context=None):
        selection = super(ShippingLabel, self)._get_file_type_selection(
            cr, uid, context=None)
        selection.append(('zpl2', 'ZPL2'))
        return selection

