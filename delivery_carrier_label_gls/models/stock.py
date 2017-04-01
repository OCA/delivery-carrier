# -*- coding: utf-8 -*-
# © 2013-2015 David BEAL <david.beal@akretion.com>
# © 2017 Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields, _
from ..report.label import GLSLabel, InvalidDataForMako
from ..report.exception_helper import (InvalidAccountNumber)
from ..report.label_helper import (
    InvalidValueNotInList,
    InvalidMissingField,
    InvalidType,)
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import pycountry
from operator import attrgetter


EXCEPT_TITLE = "GLS Library Exception"
LABEL_TYPE = 'zpl2'


def raise_exception(message):
    raise Warning("%s\n%s" % (EXCEPT_TITLE, map_except_message(message)))


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

    @api.multi
    def action_done(self):
        """
        :return: see original method
        """
        self.filtered(lambda picking: picking.carrier_type == 'gls'
                      ).generate_labels()
        return super(StockPicking, self).action_done()

    @api.multi
    def _customize_gls_picking(self):
        "Use this method to override gls picking"
        return True

    @api.model
    def _prepare_global_gls(self):
        param_m = self.env['ir.config_parameter']
        gls_keys = ['carrier_gls_warehouse', 'carrier_gls_customer_code']
        params = param_m.search([('key', 'in', gls_keys)])
        return {elm.key: elm.value for elm in params}

    @api.model
    def _prepare_address_name_gls(self):
        partner = self.partner_id
        consignee = partner.name
        contact = partner.name
        if partner.parent_id and partner.use_parent_address:
            consignee = partner.parent_id.name
        return {'consignee_name': consignee, 'contact': contact}

    @api.multi
    def _prepare_address_gls(self):
        self.ensure_one()
        address = {}
        res = self.partner_id._get_split_address(3, 35)
        address['street'], address['street2'], address['street3'] = res
        country_code = (self.partner_id and
                        self.partner_id.country_id.code or 'FR')
        iso_3166 = pycountry.countries.get(alpha2=country_code).numeric
        address.update({
            "zip": self.partner_id.zip,
            "city": self.partner_id.city,
            "consignee_phone": self.partner_id.phone,
            "consignee_mobile": (self.partner_id.mobile or
                                 self.partner_id.phone),
            "consignee_email": self.partner_id.email,
            "country_code": self.partner_id.country_id.code or 'FR',
            # useful uniship label only
            "country_norme3166": int(iso_3166),
        })
        destination = self._prepare_address_name_gls()
        address['consignee_name'] = destination['consignee_name'][:35]
        address['contact'] = destination['contact'][:35]
        return address

    @api.multi
    def _prepare_delivery_gls(self, number_of_packages):
        self.ensure_one()
        shipping_date = self.min_date or self.date
        shipping_date = fields.Datetime.from_string(shipping_date)
        delivery = {
            'consignee_ref': self.name[:20],
            'additional_ref_1': u'',
            'additional_ref_2': self.name[:20],
            'shipping_date': shipping_date.strftime('%Y%m%d'),
            'commentary': self.note,
            'parcel_total_number': number_of_packages,
        }
        return delivery

    @api.multi
    def _prepare_sender_gls(self):
        self.ensure_one()
        partner = self._get_label_sender_address()
        global_infos = self._prepare_global_gls()
        sender = {'contact_id': self.company_id.gls_fr_contact_id,
                  'customer_id': global_infos['carrier_gls_customer_code'],
                  'contact_id_inter': self.company_id.gls_inter_contact_id,
                  'outbound_depot': global_infos['carrier_gls_warehouse']}
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

    @api.multi
    def _prepare_pack_gls(self, pack_number, weight=None):
        self.ensure_one()
        pack = {
            'parcel_number_label': pack_number,
            'parcel_number_barcode': pack_number,
            'custom_sequence': self._get_sequence('gls'),
        }
        if weight:
            pack.update({
                'weight': "{0:05.2f}".format(weight),
            })
        else:
            if self.move_ids:
                tracking_weight = [move.weight
                                   for move in self.move_ids][0]
                pack.update({
                    'weight': "{0:05.2f}".format(tracking_weight),
                })
        return pack

    @api.multi
    def _get_tracking_ids_from_moves(self):
        """ get all the trackings of the picking
            no tracking_id will return a False (Browse Null), meaning that
            we want a label for the picking
        """
        self.ensure_one()
        return sorted(set(
            line.tracking_id for line in self.move_lines
        ), key=attrgetter('name'))

    @api.multi
    def _get_weight_from_moves_without_tracking(self):
        weights = [line.weight for line in self.move_lines
                   if not line.tracking_id]
        return sum(weights)

    @api.multi
    def _generate_gls_labels(self, service, trackings=False):
        """ Generate labels and write tracking numbers received """
        pack_nbr = 0
        pick2update = {}
        address = self._prepare_address_gls()
        if not trackings:
            trackings = self._get_tracking_ids_from_moves()
        labels = []
        without_track = 0
        for track in trackings:
            if not track:
                without_track += 1
        pick2update['number_of_packages'] = len(trackings) - without_track + 1
        delivery = self._prepare_delivery_gls(
            pick2update['number_of_packages'])
        # Write tracking_number on serial field
        # for move lines with tracking
        # and on picking for other moves
        for packing in trackings:
            pack_nbr += 1
            addr = address.copy()
            deliv = delivery.copy()
            if not packing:
                without_track -= 1
                if without_track > 0:
                    continue
                # only executed for the last move line with no tracking
                weight = self._get_weight_from_moves_without_tracking()
                pack = self._prepare_pack_gls(pack_nbr, weight=weight)
                label = self.get_zpl(service, deliv, addr, pack)
                pick2update['carrier_tracking_ref'] = label['tracking_number']
            else:
                pack = self._prepare_pack_gls(pack_nbr)
                label = self.get_zpl(service, deliv, addr, pack)
                packing.write({'serial': label['tracking_number']})
            label_info = {
                'tracking_id': packing.id if packing else False,
                'file': label['content'],
                'file_type': LABEL_TYPE,
                'name': label['filename'] + '.zpl',
            }
            if label['tracking_number']:
                label_info['name'] = '%s%s.zpl' % (label['tracking_number'],
                                                   label['filename'])
            labels.append(label_info)
        # must be on this stock.picking.out to event on connector
        # like in modules prestahop or magento
        self.write(pick2update)
        self._customize_gls_picking()
        return labels

    @api.model
    def get_zpl(self, service, delivery, address, pack):
        try:
            result = service.get_label(delivery, address, pack)
        except (InvalidMissingField,
                InvalidDataForMako,
                InvalidValueNotInList,
                InvalidAccountNumber,
                InvalidType) as e:
            raise_exception(e.message)
        except Exception, e:
            raise Warning("%s\n%s" % (EXCEPT_TITLE, e.message))
        return result

    @api.multi
    def generate_shipping_labels(self, tracking_ids=None):
        """ Add label generation for GLS """
        self.ensure_one()
        if self.carrier_id.type == 'gls':
            sender = self._prepare_sender_gls()
            # gls has a rescue label without webservice required
            # if webservice is down
            # rescue label is also used for international carrier
            test = False
            if self.company_id.gls_test:
                test = True
            try:
                service = GLSLabel(
                    sender, self.carrier_code, test_plateform=test)
            except InvalidMissingField as e:
                raise_exception(e.message)
            except Exception as e:
                raise_exception(e.message)
            return self._generate_gls_labels(
                service, tracking_ids=tracking_ids)
        return super(StockPicking, self).\
            generate_shipping_labels(tracking_ids=tracking_ids)

    @api.model
    def _get_sequence(self, label_name):
        sequence = self.env['ir.sequence'].next_by_code(
            'stock.picking_' + label_name)
        if not sequence:
            title = _("Picking sequence"),
            message = _(
                "There is no sequence defined for the label '%s'") % label_name
            raise Warning("%s\n%s" % (title, message))
        return sequence

    @api.multi
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default.update({
            'carrier_tracking_ref': None,
        })
        return super(StockPickingOut, self).copy(default)

    @api.multi
    def get_shipping_cost(self):
        return 0


class ShippingLabel(models.Model):
    _inherit = 'shipping.label'

    @api.model
    def _get_file_type_selection(self):
        selection = super(ShippingLabel, self)._get_file_type_selection()
        selection.append(('zpl2', 'ZPL2'))
        selection = list(set(selection))
        return selection
