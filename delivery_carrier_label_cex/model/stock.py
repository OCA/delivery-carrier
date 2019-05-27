from odoo import models, api, fields, _
from datetime import date
from unidecode import unidecode
from openerp.exceptions import Warning
import requests
import re
import json


class ShippingLabel(models.Model):
    _inherit = 'shipping.label'

    @api.model
    def _get_file_type_selection(self):
        """ To inherit to add file type """
        res = super(ShippingLabel, self)._get_file_type_selection()
        res.append(('txt', 'TXT'))
        res = list(set(res))
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cex_result = fields.Char(
        string='CEX Status')

    @api.multi
    def _generate_cex_label(self, package_ids=None):
        self.ensure_one()

        url = self.company_id.cex_test and \
            'https://test.correosexpress.com/wspsc/apiRestGrabacionEnvio'\
            '/json/grabacionEnvio' or \
            'https://www.correosexpress.com/wpsc/apiRestGrabacionEnvio/'\
            'json/grabacionEnvio'
        username = self.company_id.cex_username
        password = self.company_id.cex_password
        data = self._get_cex_label_data()
        try:
            response = requests.post(url, auth=(
                username, password), json=data, timeout=5)
            rjson = json.loads(re.search('({.*})', response.text).group(1))
        except requests.exceptions.Timeout:
            rjson = {'codigoRetorno': 999,
                     'mensajeRetorno': '\n\nEl servidor está tardando mucho en responder.'.decode('utf-8')}
        except:
            rjson = {'codigoRetorno': 999,
                     'mensajeRetorno': '\n\n' + response.text}
        retorno = rjson['codigoRetorno']
        message = rjson['mensajeRetorno']

        if retorno == 0:
            self.carrier_tracking_ref = rjson['datosResultado']
            self.cex_result = rjson['etiqueta'][0]['etiqueta2']
            return [{
                'name': self.name + '_' + self.carrier_tracking_ref + '.txt',
                'file': self.cex_result,
                'file_type': 'txt'
            }]
        else:
            raise Warning(_("CEX Error: %s %s") %
                          (retorno or 999, message or 'Webservice ERROR.'))

        return False

    @api.multi
    def number_of_packages_for_cex(self):
        self.ensure_one()
        # TODO check pack operation no disponible en v 12
        return len(self.pack_operation_product_ids.mapped('result_package_id'))

    def _get_cex_label_data(self):
        self.ensure_one()

        partner = self.partner_id
        number_of_packages = self.number_of_packages_for_cex() or 1
        phone = partner.mobile or partner.phone or ''
        listaBultos = []
        for i in range(0, number_of_packages):
            listaBultos.append({
                'ancho': '',
                'observaciones': '',
                'kilos': '',
                'codBultoCli': '',
                'codUnico': '',
                'descripcion': '',
                'alto': '',
                'orden': i + 1,
                'referencia': '',
                'volumen': '',
                'largo': ''
            })

        streets = []
        if partner.street:
            streets.append(unidecode(partner.street))
        if partner.street2:
            streets.append(unidecode(partner.street2))

        data = {
            'solicitante': self.company_id.cex_solicitante,
            'canalEntrada': '',
            'numEnvio': '',
            'ref': self.origin[:20],
            'refCliente': '',
            'fecha': date.today().strftime('%d%m%Y'),
            'codRte': self.company_id.cex_codRte,
            'nomRte': self.company_id.name,
            'nifRte': '',
            'dirRte': self.company_id.street,
            'pobRte': self.company_id.city,
            'codPosNacRte': self.company_id.zip,
            'paisISORte': '',
            'codPosIntRte': '',
            'contacRte': self.company_id.name,
            'telefRte': self.company_id.phone,
            'emailRte': self.company_id.email,
            'codDest': '',
            'nomDest': partner.name[:40] or '',
            'nifDest': '',
            'dirDest': ''.join(streets)[:300],
            'pobDest': partner.city[:50] or '',
            'codPosNacDest': partner.zip,
            'paisISODest': '',
            'codPosIntDest': '',
            'contacDest': partner.name[:40] or '',
            'telefDest': phone[:15],
            'emailDest': partner.email[:75] or '',
            'contacOtrs': '',
            'telefOtrs': '',
            'emailOtrs': '',
            'observac': '',
            'numBultos': number_of_packages or 1,
            'kilos': '%.3f' % (self.weight or 1),
            'volumen': '',
            'alto': '',
            'largo': '',
            'ancho': '',
            'producto': '93',
            'portes': 'P',
            'reembolso': '',  # TODO cash_on_delivery
            'entrSabado': '',
            'seguro': '',
            'numEnvioVuelta': '',
            'listaBultos': listaBultos,
            'codDirecDestino': '',
            'password': 'string',
            'listaInformacionAdicional': [{
                'tipoEtiqueta': '2',
                'etiquetaPDF': ''
            }],
        }

        return data

    @api.multi
    def _generate_cex_labels(self, package_ids=None):
        """ Generate the labels.
        A list of package ids can be given, in that case it will generate
        the labels only of these packages.
        """
        label_obj = self.env['shipping.label']

        for pick in self:
            if package_ids:
                shipping_labels = pick._generate_cex_label(
                    package_ids=package_ids
                )
            else:
                shipping_labels = pick._generate_cex_label()
            for label in shipping_labels:
                data = {
                    'name': label['name'],
                    'datas_fname': label.get('filename', label['name']),
                    'res_id': pick.id,
                    'res_model': 'stock.picking',
                    'datas': label['file'].encode('base64'),
                    'file_type': label['file_type'],
                }
                if label.get('package_id'):
                    data['package_id'] = label['package_id']
                context_attachment = self.env.context.copy()
                printer = self.env.user.printing_printer_id or \
                    self.env['printing.printer'].get_default()
                printer.print_document(
                    None, label['file'], 'raw')
                # remove default_type setted for stock_picking
                # as it would try to define default value of attachement
                if 'default_type' in context_attachment:
                    del context_attachment['default_type']
                label_obj.with_context(context_attachment).create(data)
        return True

    @api.multi
    def generate_cex_labels(self, package_ids=None):
        """ Add label generation for CEX """
        self.ensure_one()
        if self.carrier_id.carrier_type == 'cex':
            return self._generate_cex_labels(package_ids=package_ids)
        return super(StockPicking, self).generate_default_label(
            package_ids=package_ids)

    @api.multi
    def do_new_transfer(self):
        if self.carrier_id.carrier_type == 'cex':
            self.generate_cex_labels()
        return super(StockPicking, self).do_new_transfer()
