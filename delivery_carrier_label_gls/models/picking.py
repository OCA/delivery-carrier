# coding: utf-8
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
import base64
import logging

from openerp import models, api, fields, _
from openerp.exceptions import Warning as UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from ..report.label import GLSLabel, InvalidDataForMako
from ..report.exception_helper import (InvalidAccountNumber)
from ..report.label_helper import (
    InvalidValueNotInList,
    InvalidMissingField,
    InvalidType,)

_logger = logging.getLogger(__name__)

try:
    import pycountry
except (ImportError, IOError) as err:
    _logger.debug(err)


def raise_exception(message):
    raise UserError(map_except_message(message))


def map_except_message(message):
    """ Allows to map vocabulary from external library
        to Odoo vocabulary in Exception message
    """
    model_mapping = {
        'shipper_country': 'partner_id.country_id.code',
        'customer_id': 'France or International field '
                       '(settings > config > carrier > GLS)',
    }
    for key, val in model_mapping.items():
        message = message.replace(key, val)
    return message


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_tracking_ref = fields.Char(copy=False)

    @api.multi
    def do_transfer(self):
        """ Used by wizard stock_tranfert_details and js interface """
        res = super(StockPicking, self).do_transfer()
        for picking in self:
            if picking.carrier_type == 'gls':
                picking.label_subtask()
        return res

    @api.multi
    def action_done(self):
        """ Used by stock_picking_wave """
        res = super(StockPicking, self).action_done()
        for picking in self:
            if picking.carrier_type == 'gls':
                picking.label_subtask()
        return res

    @api.multi
    def label_subtask(self):
        self.ensure_one()
        self.set_pack_weight()
        if self.company_id.gls_generate_label:
            self.generate_labels()

    @api.multi
    def _customize_gls_picking(self):
        "Use this method to override gls picking"
        self.ensure_one()
        return True

    @api.model
    def _prepare_global_gls(self):
        res = {}
        param_m = self.env['ir.config_parameter']
        gls_keys = ['carrier_gls_warehouse', 'carrier_gls_customer_code']
        configs = param_m.search([('key', 'in', gls_keys)])
        for elm in configs:
            res[elm.key] = elm.value
        return res

    @api.model
    def _prepare_address_name_gls(self, partner):
        consignee = partner.name
        contact = partner.name
        if partner.parent_id and partner.use_parent_address:
            consignee = partner.parent_id.name
        return {'consignee_name': consignee, 'contact': contact}

    @api.multi
    def _prepare_address_gls(self):
        self.ensure_one()
        address = {}
        res = self.env['res.partner']._get_split_address(
            self.partner_id, 3, 35)
        address['street'], address['street2'], address['street3'] = res
        country_code = (self.partner_id and
                        self.partner_id.country_id.code or 'FR')
        iso_3166 = pycountry.countries.get(alpha_2=country_code).numeric
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
        destination = self._prepare_address_name_gls(self.partner_id)
        address['consignee_name'] = destination['consignee_name'][:35]
        address['contact'] = destination['contact'][:35]
        return address

    @api.multi
    def _prepare_delivery_gls(self, number_of_packages):
        self.ensure_one()
        shipping_date = self.min_date or self.date
        shipping_date = datetime.strptime(
            shipping_date, DEFAULT_SERVER_DATETIME_FORMAT)
        delivery = {}
        delivery.update({
            'consignee_ref': self.name[:20],
            'additional_ref_1': u'',
            'additional_ref_2': self.name[:20],
            'shipping_date': shipping_date.strftime('%Y%m%d'),
            'commentary': self.note,
            'parcel_total_number': number_of_packages,
        })
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

    @api.model
    def _prepare_pack_gls(self, package, pack_number):
        return {
            'parcel_number_label': pack_number,
            'parcel_number_barcode': pack_number,
            'custom_sequence': self._get_sequence('gls'),
            'weight': "{0:05.2f}".format(package.weight)
        }

    @api.multi
    def _generate_gls_labels(self, service, packages=None):
        """ Generate labels and write tracking numbers received """
        self.ensure_one()
        pack_number = 0
        deliv = {}
        traceability = []
        labels = []
        address = self._prepare_address_gls()
        if packages is None:
            packages = self._get_packages_from_picking()
        delivery = self._prepare_delivery_gls(len(packages))
        for package in packages:
            pack_number += 1
            addr = address.copy()
            deliv.clear()
            deliv = delivery.copy()
            pack = self._prepare_pack_gls(package, pack_number)
            label = self.get_zpl(service, deliv, addr, pack)
            pack_vals = {'parcel_tracking': label['tracking_number'],
                         'carrier_id': self.carrier_id.id}
            package.write(pack_vals)
            _logger.info("package wrote")
            label_info = {
                'package_id': package.id,
                'file': label['content'],
                'file_type': 'zpl2',
                'type': 'binary',
                'name': label['filename'] + '.zpl',
            }
            if label['tracking_number']:
                label_info['name'] = '%s%s.zpl' % (label['tracking_number'],
                                                   label['filename'])
            if self.company_id.country_id.code == 'FR':
                labels.append(label_info)
            traceability.append(self._record_webservice_exchange(label, pack))
        self.write({'number_of_packages': pack_number})
        if self.company_id.gls_traceability and traceability:
            self._save_traceability(traceability, label)
        self._customize_gls_picking()
        return labels

    @api.multi
    def _save_traceability(self, traceability, label):
        self.ensure_one()
        separator = '=*' * 40
        content = u'\n\n%s\n\n\n' % separator
        content = content.join(traceability)
        content = (
            u'Company: %s\nCompte France: %s \nCompte Etranger: %s \n\n\n') % (
            self.company_id.name or '',
            self.company_id.gls_fr_contact_id or '',
            self.company_id.gls_inter_contact_id or '') + content
        data = {
            'name': u'GLS_traceability.txt',
            'res_id': self.id,
            'res_model': self._name,
            'datas': base64.b64encode(content.encode('utf8')),
            'type': 'binary',
            'file_type': 'text/plain',
        }
        return self.env['shipping.label'].create(data)

    def _record_webservice_exchange(self, label, pack):
        trac_infos = ''
        if 'raw_response' in label and 'request' in label:
            trac_infos = (
                u'Sequence Colis GLS:\n====================\n%s \n\n'
                u'Web Service Request:\n====================\n%s \n\n'
                u'Web Service Response:\n=====================\n%s \n\n') % (
                pack['custom_sequence'],
                label['request'],
                label['raw_response'])
        return trac_infos

    def get_zpl(self, service, delivery, address, pack):
        try:
            _logger.info(
                "GLS label generating for delivery '%s', pack '%s'",
                delivery['consignee_ref'], pack['parcel_number_label'])
            result = service.get_label(delivery, address, pack)
        except (InvalidMissingField,
                InvalidDataForMako,
                InvalidValueNotInList,
                InvalidAccountNumber,
                InvalidType) as e:
            raise_exception(e.message)
        except Exception, e:
            raise UserError(e.message)
        return result

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """ Add label generation for GLS """
        self.ensure_one()
        if self.carrier_type == 'gls':
            sender = self._prepare_sender_gls()
            # gls has a rescue label without webservice required
            # if webservice is down
            # rescue label is also used for international carrier
            test = False
            if self.company_id.gls_test:
                test = True
            try:
                _logger.info(
                    "Connecting to GLS web service")
                service = GLSLabel(
                    sender, self.carrier_code, test_plateform=test)
            except InvalidMissingField as e:
                raise_exception(e.message)
            except Exception as e:
                raise_exception(e.message)
            self._check_existing_shipping_label()
            return self._generate_gls_labels(
                service, packages=package_ids)
        return (super(StockPicking, self)
                .generate_shipping_labels(package_ids=package_ids))

    @api.model
    def _get_sequence(self, label_name):
        sequence = self.env['ir.sequence'].next_by_code(
            'stock.picking_%s' % label_name)
        if not sequence:
            raise UserError(
                _("There is no sequence defined for the label '%s'")
                % label_name)
        return sequence

    @api.multi
    def get_shipping_cost(self):
        return 0
