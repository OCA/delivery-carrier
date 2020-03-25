import base64
import html
import logging
import os
import re
import time
from tempfile import NamedTemporaryFile

import requests

import inema  # pip3 install git+https://gitlab.com/gsauthof/python-inema.git
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval as eval

from . import pypdftk

# please set the path as per pdftk installed on OS
# pypdftk.PDFTK_PATH = '/usr/local/bin/pdftk'

KEY_PHASE = "1"
prod_code_with_tracking = ['1022']


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(html.entities.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is

    return re.sub(r"&#?\w+;", fixup, text)


class CarrierAccount(models.Model):
    _inherit = 'carrier.account'

    partner_id = fields.Char('Partner ID')
    partner_key = fields.Char('Partner Key')
    file_format = fields.Selection(
        selection='_selection_file_format', string='File Format',
        help="Default format of the carrier's label you want to print",
        required=True, default="26")
    type = fields.Selection(
        selection='_get_carrier_type', required=True,
        help="In case of several carriers, help to know which account "
             "belong to which carrier")

    @api.model
    def _selection_file_format(self):
        resp = super(CarrierAccount, self)._selection_file_format()
        for fmt in inema.inema.formats:
            resp.append((str(fmt['id']), "[%s] %s" % (fmt['id'], fmt['name'])))
        return resp

    def _get_carrier_type(self):
        resp = []
        resp.append(('deutsche_post', 'Deutsche Post'))
        return resp

    @api.multi
    def test_connection(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'File',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'download.file',
            'target': 'new',
        }

    @api.multi
    def view_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'de.post.logs',
            'view_type': 'form',
            "view_mode": 'tree,form',
            'target': 'current',
        }

    @api.multi
    def get_label(self, data, preview=False):

        if not data.get('prod_code'):
            raise UserError(_("Product Code required"))

        if data['prod_code'] not in [k for k in inema.inema.marke_products]:
            raise UserError(_("Product Code %s does not exist") % (data['prod_code']))

        logging.basicConfig(level=logging.INFO)
        im = inema.Internetmarke(self.partner_id, self.partner_key, KEY_PHASE)
        try:
            im.authenticate(self.account, self.password)
        except Exception as e:
            raise UserError(_(str(e)))
        sysmo_addr = im.build_addr(
            street=data['source']['street2'],
            house='', zipcode=data['source']['zip'],
            city=data['source']['city'],
            country=data['source']['country'],
            additional=data['source']['street'])
        sysmo_naddr = im.build_comp_addr(
            company=data['source']['name'], address=sysmo_addr)

        if data['dest']['street'] and data['dest']['street2']:
            street = data['dest']['street2']
            additional = data['dest']['street']
        elif data['dest']['street']:
            street = data['dest']['street']
            additional = ''
        elif data['dest']['street2']:
            street = data['dest']['street2']
            additional = ''
        else:
            raise UserError(_("Street missing in address"))

        city = ''
        if data['dest']['state'] and data['dest']['city']:
            city = data['dest']['city'] + ', ' + data['dest']['state']
        elif data['dest']['city']:
            city = data['dest']['city']
        elif data['dest']['state']:
            city = data['dest']['state']

        dest_addr = im.build_addr(
            street=street, house='', zipcode=data['dest']['zip'],
            city=city, country=data['dest']['country'], additional=additional)

        if not data['dest']['company']:
            dest_naddr = im.build_pers_addr(
                first=data['dest']['first'], last=data['dest']['last'],
                address=dest_addr, salutation=None,
                title=data['dest']['title'])
        else:
            person = im.build_pers_name(
                first=data['dest']['first'], last=data['dest']['last'],
                salutation=None, title=data['dest']['title'])
            dest_naddr = im.build_comp_addr(
                company=data['dest']['company'], address=dest_addr,
                person=person)

        position = im.build_position(
            product=data['prod_code'], sender=sysmo_naddr,
            receiver=dest_naddr, layout="AddressZone",
            pdf=True, x=1, y=1, page=1)
        im.add_position(position)

        if preview:
            resp_data = im.retrievePreviewPDF(
                data['prod_code'], self.file_format, layout="AddressZone")
            response = requests.get(resp_data)

            file_name = "Test"
            file_data = response.content
        else:
            try:
                resp_data = im.checkoutPDF(self.file_format)
            except Exception as e:
                raise UserError(_('Deutsche Post Checkout Error'), e)

            voucher = resp_data['shoppingCart']['voucherList']['voucher'][0]
            file_name = voucher['trackId']
            if not file_name and data['prod_code'] in prod_code_with_tracking:
                file_name = voucher['voucherId']
            file_data = resp_data['pdf_bin']

        self.env['de.post.logs'].create({
            'prod_code': data['prod_code'],
            'format_code': self.file_format,
            'request': "%s\n%s" % (str(sysmo_naddr), str(dest_naddr)),
            'response': resp_data,
            'name': data['name'],
            'account_id': self.id,
            'tracking_num': file_name,
        })

        return file_name, base64.encodestring(file_data)

    @api.multi
    def view_forms(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'carrier.form',
            'view_type': 'form',
            "view_mode": 'tree,form',
            'target': 'current',
        }


class DownloadFile(models.TransientModel):
    _name = 'download.file'
    _description = 'Download File'

    file = fields.Binary('File', readonly="1")
    file_name = fields.Char('File Name')
    prod_code = fields.Char('Prod Code', default=147)
    picking_id = fields.Many2one('stock.picking', 'Test Picking')

    @api.multi
    def test_connection(self):
        test_data = {
            'name': 'Test/Preview',
            'prod_code': self.prod_code,
            'dest': {
                'first': '',
                'last': 'Herald Welte',
                'street': 'Glanzstrasse 11',
                'street2': '',
                'zip': '12437',
                'city': 'Berlin',
                'state': '',
                'country': '',
                'title': 'Mr.',
                'company': 'Orange GmbH',

            },
            'source': {
                'name': self.env.user.company_id.name,
                'street': self.env.user.company_id.street or '',
                'street2': self.env.user.company_id.street2 or '',
                'zip': self.env.user.company_id.zip or '',
                'city': "%s - %s" % (
                    self.env.user.company_id.city,
                    self.env.user.company_id.country_id.name),
                'country': self.env.user.company_id.country_id.code_iso or '',
            }
        }
        file_name, file_data = self.env['carrier.account'].browse(
            self._context['active_id']).get_label(test_data, preview=True)

        carrier_form = self.env['carrier.form'].search(
            [('prod_code', '=', self.prod_code)])
        if carrier_form:
            file_data = carrier_form.append_carrier_form(
                file_data, self.picking_id)

        self.write({
            'file': file_data,
            'file_name': (file_name or '_Download_') + '.pdf'
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'File',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'download.file',
            'target': 'new',
            'res_id': self.id,
        }


class DeutschePostLogs(models.Model):
    _name = 'de.post.logs'
    _description = 'Deutsche Post Logs'
    _order = 'create_date desc'

    prod_code = fields.Char('Product Code')
    format_code = fields.Char('Format Code')
    account_id = fields.Many2one('carrier.account', 'Carrier Account')
    tracking_num = fields.Char('Tracking ID')
    name = fields.Char('Name')
    request = fields.Text('Request')
    response = fields.Text('Response/URL')


class CarrierForm(models.Model):
    _name = 'carrier.form'
    _description = 'Deutsche Carrier Form'
    
    prod_code = fields.Char('Deutsche Label Product Code')
    pdf_file_id = fields.Many2one('ir.attachment', 'Form PDF')
    field_ids = fields.One2many(
        'carrier.form.field', 'form_id', string='Variables')

    @api.multi
    def append_carrier_form(self, label_pdf, picking=False):
        label_file = NamedTemporaryFile(delete=False)
        source_file = NamedTemporaryFile(delete=False)
        flatten_file = NamedTemporaryFile(delete=False)
        merged_file = NamedTemporaryFile(delete=False)

        with open(label_file.name, "wb") as f:
            f.write(base64.b64decode(label_pdf)) #label_pdf.decode('base64')
            label_file.close()

        with open(source_file.name, "wb") as f:
            f.write(base64.b64decode(self.pdf_file_id.datas)) #self.pdf_file_id.datas.decode('base64')
            source_file.close()

        datas = {}
        eval_context = {
            'picking': picking, 'self': self,
            'user': self.env.user, 'time': time}
        for var in self.field_ids:
            eval(var.code.strip(), eval_context, mode="exec", nocopy=True)
            if 'result' in eval_context:
                datas[var.name] = eval_context['result']

        pypdftk.fill_form(
            source_file.name, datas=datas, out_file=flatten_file.name,
            flatten=True)

        pypdftk.concat(
            [label_file.name, flatten_file.name], out_file=merged_file.name)

        fp = open(merged_file.name, "rb")
        merged_file_data = fp.read()
        fp.close()

        os.unlink(label_file.name)
        os.unlink(source_file.name)
        os.unlink(flatten_file.name)
        os.unlink(merged_file.name)

        return base64.encodestring(merged_file_data)

    @api.multi
    def find_fields(self):
        self.ensure_one()

        source_file = NamedTemporaryFile(delete=False)
        with open(source_file.name, "wb") as f:
            f.write(self.pdf_file_id.datas.decode('base64'))
            source_file.close()

        resp = pypdftk.run_command(
            [pypdftk.PDFTK_PATH, source_file.name, 'dump_data_fields'])

        for fld in resp:
            fld_parts = fld.split(':')
            if fld_parts[0] == 'FieldName':
                fld_name = unescape(fld_parts[1].strip())
                if not self.env['carrier.form.field'].search(
                        [('name', '=', fld_name), ('form_id', '=', self.id)]):
                    self.env['carrier.form.field'].create({
                        'name': fld_name,
                        'form_id': self.id
                    })

        os.unlink(source_file.name)


class CarrierFormField(models.Model):
    _name = 'carrier.form.field'
    _description = 'Deutsche Post Form Field'
    
    form_id = fields.Many2one('carrier.form', 'From', required=1)
    name = fields.Char('Form Variable Name', required=1)
    code = fields.Text('Code', required=1, default='result=""')
