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
    InvalidValueNotInList,
    InvalidMissingField,
    InvalidType,)
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import pycountry
from operator import attrgetter


EXCEPT_TITLE = "GLS Library Exception"
LABEL_TYPE = 'zpl2'


def raise_exception(orm, message):
    raise orm.except_orm(EXCEPT_TITLE, map_except_message(message))


def map_except_message(message):
    """ Allows to map vocabulary from external library
        to Odoo vocabulary in Exception message
    """
    model_mapping = {
        'shipper_country': 'partner_id.country_id.code',
        #'shipper_zip': 'zip',
    }
    for key, val in model_mapping.items():
        message = message.replace(key, val)
    #if "field 'country_code' with value 'None' must belong" in message:
    #    message = _("partner ")
    return message


class StockPicking(orm.Model):
    _inherit = "stock.picking"

    def action_done(self, cr, uid, ids, context=None):
        """
        :return: see original method
        """
        #TODO recreate context
        if context is None:
            context = {}
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.carrier_type == 'gls':
                self.generate_labels(
                    cr, uid, [picking.id], context=context)
        return super(StockPicking, self).action_done(
            cr, uid, ids, context=context)

    def generate_shipping_labels(self, cr, uid, ids, tracking_ids=None,
                                 context=None):
        return self.pool['stock.picking.out'].generate_shipping_labels(
            cr, uid, ids, tracking_ids=tracking_ids, context=context)


class StockPickingOut(orm.Model):
    _inherit = 'stock.picking.out'

    def _prepare_address_gls(self, cr, uid, picking, context=None):
        address = {}
        res = self.pool['res.partner']._get_split_address(
            cr, uid, picking.partner_id, 3, 35, context=context)
        address['street'], address['street2'], address['street3'] = res
        country_code = (picking.partner_id and
                        picking.partner_id.country_id.code or 'FR')
        iso_3166 = pycountry.countries.get(alpha2=country_code).numeric
        address.update({
            "consignee_name": picking.partner_id.name,
            "zip": picking.partner_id.zip,
            "city": picking.partner_id.city,
            "consignee_phone": picking.partner_id.phone,
            "consignee_mobile": picking.partner_id.mobile,
            "consignee_email": picking.partner_id.email,
            "country_code": picking.partner_id.country_id.code or 'FR',
            # useful uniship label only
            "country_norme3166": int(iso_3166),
        })
        return address

    def _prepare_sender_gls(self, cr, uid, pick, context=None):
        partner = self.pool['stock.picking.out']._get_label_sender_address(
            cr, uid, pick, context=context)
        sender = {'customer_id': pick.company_id.gls_customer_code,
                  'contact_id': pick.company_id.gls_contact_id,
                  'outbound_depot': pick.company_id.gls_warehouse_code}
        if partner.country_id:
            sender['country'] = partner.country_id.name
        sender.update({
            'shipper_street': partner.street,
            'shipper_street2': partner.street2,
            'shipper_name': partner.name,
            'shipper_country': partner.country_id.code,
            'shipper_zip': partner.zip,
            'shipper_city': partner.city,
            })
        return sender

    def _prepare_delivery_gls(self, cr, uid, picking, context=None):
        shipping_date = picking.min_date
        if picking.date_done:
            shipping_date = picking.date_done
        shipping_date = datetime.strptime(
            shipping_date, DEFAULT_SERVER_DATETIME_FORMAT)
        delivery = {}
        delivery.update({
            "contact": picking.company_id.name,
            'consignee_ref': picking.name,
            'additional_ref_1': u'',
            'additional_ref_2': picking.name,
            'shipping_date': shipping_date.strftime('%Y%m%d'),
            'commentary': picking.note,
            'parcel_total_number': picking.number_of_packages,
            'custom_sequence': self._get_sequence(
                cr, uid, 'gls', context=context),
            })
        return delivery

    def _prepare_pack_gls(
            self, cr, uid, tracking, pack_number, weight, context=None):
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
            tracking_weight = [move.weight for move in tracking.move_ids][0]
            pack.update({
                'weight': "{0:05.2f}".format(tracking_weight),
                })
        return pack

    def _get_tracking_ids_from_moves(self, cr, uid, picking, context=None):
        """ get all the trackings of the picking
            no tracking_id will return a False, meaning that
            we want a label for the picking
        """
        return sorted(set(
            line.tracking_id for line in picking.move_lines
        ), key=attrgetter('name'))

    def _generate_gls_label(
            self, cr, uid, picking, service, tracking_ids=None, context=None):
        """ Generate labels and write tracking numbers received """
        address = self._prepare_address_gls(cr, uid, picking, context=context)
        if tracking_ids is None:
            trackings = self._get_tracking_ids_from_moves(
                cr, uid, picking, context=context)
        else:
            # restrict on the provided trackings
            trackings = self.pool['stock.tracking'].browse(
                cr, uid, tracking_ids, context=context)
        labels = []
        picking.write({'number_of_packages': len(trackings)})
        picking = self.browse(cr, uid, picking.id, context=context)
        delivery = self._prepare_delivery_gls(
            cr, uid, picking, context=context)
        pack_number = 0
        # if there are no pack defined, write tracking_number on picking
        # otherwise, write it on serial field of each pack
        for parcel in trackings:
            pack_number += 1
            addr = address.copy()
            deliv = delivery.copy()
            if not parcel:
                # ignore lines without tracking when there is tracking
                # in a picking
                # Example: if I have 1 move with a tracking and 1
                # without, I will have [False, a_tracking] in
                # `trackings`. In that case, we are using packs, not the
                # picking for the tracking numbers.
                if len(trackings) > 1:
                    continue
                pack = self._prepare_pack_gls(
                    cr, uid, parcel, pack_number, picking.weight, context=context)
                label = self.get_zpl(service, deliv, addr, pack)
                self.write(cr, uid, picking.id,
                           {'carrier_tracking_ref': label['tracking_number']},
                           context=context)
            else:
                pack = self._prepare_pack_gls(
                    cr, uid, parcel, pack_number, None, context=context)
                label = self.get_zpl(service, deliv, addr, pack)

                #for search_label in res['value']:
                #    if track.name in search_label['item_id'].split('+')[-1]:
                #        label = search_label
                #        tracking_number = label['tracking_number']
                #        track.write({'serial': label['tracking_number']})
                #        break

                parcel.write({'serial': label['tracking_number']})
            labels.append({
                'tracking_id': parcel.id if parcel else False,
                'file': label['content'],
                'file_type': LABEL_TYPE,
                'name': label['tracking_number'] + str(pack_number) + '.' + LABEL_TYPE,
            })
        return labels

    def get_zpl(self, service, delivery, address, pack):
        try:
            result = service.get_label(delivery, address, pack)
        except (InvalidMissingField,
                InvalidDataForMako,
                InvalidValueNotInList,
                InvalidType) as e:
            raise_exception(orm, e.message)
        except Exception, e:
            raise orm.except_orm(EXCEPT_TITLE, e.message)
        return result

    def generate_shipping_labels(
            self, cr, uid, ids, tracking_ids=None, context=None):
        """ Add label generation for GLS """
        if isinstance(ids, (long, int)):
            ids = [ids]
        assert len(ids) == 1
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking.carrier_id.type == 'gls':
            sender = self._prepare_sender_gls(
                cr, uid, picking, context=context)
            #gls has a rescue label without webservice required
            #if webservice is down
            #rescue label is also used for international carrier
            test = False
            if picking.company_id.gls_test:
                test = True
            try:
                service = Gls(
                    sender, picking.carrier_code, test_plateform=test)
            except InvalidMissingField as e:
                raise_exception(orm, e.message)
            except Exception as e:
                raise_exception(orm, e.message)
            return self._generate_gls_label(
                cr, uid, picking, service,
                tracking_ids=tracking_ids,
                context=context)
        return super(StockPicking, self).\
            generate_shipping_labels(
                cr, uid, ids, tracking_ids=tracking_ids, context=context)

    def _get_sequence(self, cr, uid, label, context=None):
        sequence = self.pool['ir.sequence'].next_by_code(
            cr, uid, 'stock.picking_' + label, context=context)
        if not sequence:
            raise orm.except_orm(
                _("Picking sequence"),
                _("There is no sequence defined for the label '%s'") % label)
        return sequence

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
            "Ask us for service proposal, http://www.akretion.com/contact")


class ShippingLabel(orm.Model):
    _inherit = 'shipping.label'

    def _get_file_type_selection(self, cr, uid, context=None):
        selection = super(ShippingLabel, self)._get_file_type_selection(
            cr, uid, context=None)
        selection.append(('zpl2', 'ZPL2'))
        selection = list(set(selection))
        return selection

