# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields
from odoo.exceptions import UserError
from xml.dom.minidom import parseString
from datetime import datetime
import urllib2
import socket
import os
import base64
try:
    import genshi
    import genshi.template
except (ImportError, IOError) as err:
    import logging
    logging.getLogger(__name__).warn('Module genshi is not available')


loader = genshi.template.TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'template'),
    auto_reload=True)


class SeurConfig(models.Model):
    _name = 'seur.config'

    name = fields.Char(required=True)
    vat = fields.Char('VAT', required=True)
    integration_code = fields.Char(required=True)
    accounting_code = fields.Char(required=True)
    franchise_code = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    file_type = fields.Selection([
        ('pdf', 'PDF'),
        ('txt', 'TXT')
    ], required=True)
    printer = fields.Many2one('printing.printer')
    seurid = fields.Char()

    def connect(self, url, xml):
        """
            Connect to the Webservices and return XML data from seur

            :param url: url service.
            :param xml: XML data.

            Return XML object
        """
        headers = {}
        request = urllib2.Request(url, xml, headers)
        try:
            response = urllib2.urlopen(request, timeout=100)
            return response.read()
        except socket.timeout:
            return
        except socket.error:
            return

    def test_connection(self):
        """
        Test connection to Seur webservices
        Send XML to Seur and return error send data
        """
        tmpl = loader.load('test_connection.xml')

        vals = {
            'username': self.username,
            'password': self.password,
            'vat': self.vat,
            'franchise': self.franchise_code,
            'seurid': self.seurid,
            }

        url = 'http://cit.seur.com/CIT-war/services/ImprimirECBWebService'
        xml = tmpl.generate(**vals).render()
        result = self.connect(url, xml)
        if not result:
            return 'timed out'
        dom = parseString(result)

        # Get message connection
        # username and password wrong, get error message
        # send a shipment error, connection successfully
        message = dom.getElementsByTagName('mensaje')
        if message:
            msg = message[0].firstChild.data
            if msg == 'ERROR':
                return 'Connection successfully'
            return msg
        return 'Not found message attribute from XML'

    def create_delivery(self, data):
        """
        Create a picking using the given data

        :param data: Dictionary of values
        :return: reference (str), label (pdf), error (str)
        """
        reference = None
        label = None
        error = None

        if self.env.context.get('pdf'):
            tmpl = loader.load('picking_send_pdf.xml')
        else:
            tmpl = loader.load('picking_send.xml')

        vals = {
            'username': self.username,
            'password': self.password,
            'vat': self.vat,
            'franchise': self.franchise_code,
            'seurid': self.seurid,
            'ci': self.integration_code,
            'ccc': self.accounting_code,
            'servicio': data.get('servicio', '1'),
            'product': data.get('product', '2'),
            'total_bultos': data.get('total_bultos', 1),
            'total_kilos': data.get('total_kilos', '1'),
            'peso_bulto': data.get('peso_bulto', '1'),
            'observaciones': data.get('observaciones', ''),
            'referencia_expedicion': data.get('referencia_expedicion', ''),
            'ref_bulto': data.get('ref_bulto', ''),
            'clave_portes': data.get('clave_portes', 'F'),
            'clave_reembolso': data.get('clave_reembolso', 'F'),
            'valor_reembolso': data.get('valor_reembolso', ''),
            'cliente_nombre': data.get('cliente_nombre', ''),
            'cliente_direccion': data.get('cliente_direccion', ''),
            'cliente_tipovia': data.get('cliente_tipovia', 'CL'),
            'cliente_tnumvia': data.get('cliente_tnumvia', 'N'),
            'cliente_numvia': data.get('cliente_numvia', '.'),
            'cliente_escalera': data.get('cliente_escalera', '.'),
            'cliente_piso': data.get('cliente_piso', '.'),
            'cliente_puerta': data.get('cliente_puerta', ''),
            'cliente_poblacion': data.get('cliente_poblacion', ''),
            'cliente_cpostal': data.get('cliente_cpostal', ''),
            'cliente_pais': data.get('cliente_pais', ''),
            'cliente_email': data.get('cliente_email', ''),
            'cliente_telefono': data.get('cliente_telefono', ''),
            'cliente_atencion': data.get('cliente_atencion', ''),
            'aviso_preaviso': data.get('aviso_preaviso', 'N'),
            'aviso_reparto': data.get('aviso_reparto', 'N'),
            'aviso_email': data.get('aviso_email', 'N'),
            'aviso_sms': data.get('aviso_sms', 'N'),
            'id_mercancia': data.get('id_mercancia', ''),
            }
        if not self.env.context.get('pdf'):
            vals['printer'] = self.env.context.get('printer', 'ZEBRA')
            vals['printer_model'] = self.env.context.get(
                'printer_model', 'LP2844-Z')
            vals['ecb_code'] = self.env.context.get('ecb_code', '2C')

        url = 'http://cit.seur.com/CIT-war/services/ImprimirECBWebService'
        xml = tmpl.generate(**vals).render()
        result = self.connect(url, xml)
        if not result:
            return reference, label, 'timed out'

        dom = parseString(result)
        # Get message error from XML
        mensaje = dom.getElementsByTagName('mensaje')
        if mensaje:
            if mensaje[0].firstChild.data != 'OK':
                error = '%s - %s' % (
                    vals['ref_bulto'], mensaje[0].firstChild.data)
                return reference, label, error

        # Get reference from XML
        ecb = dom.getElementsByTagName('ECB')
        if ecb:
            reference = ecb[0].childNodes[0].firstChild.data

        if self.env.context.get('pdf'):
            # Get PDF file from XML
            pdf = dom.getElementsByTagName('PDF')
            if pdf:
                label = pdf[0].firstChild.data
        else:
            # Get TXT file from XML
            traza = dom.getElementsByTagName('traza')
            if traza:
                label = traza[0].firstChild.data

        return reference, label, error

    def get_tracking_info(self, data):
        """
            Picking info using the given data

            :param data: Dictionary of values
            :return: info dict
        """
        tmpl = loader.load('picking_info.xml')

        vals = {
            'username': self.username,
            'password': self.password,
            'expedicion': data.get('expedicion', 'S'),
            'reference': data.get('reference'),
            'service': data.get('service', '0'),
            'public': data.get('public', 'N'),
            }

        url = 'https://ws.seur.com/webseur/services/WSConsultaExpediciones'
        xml = tmpl.generate(**vals).render()
        result = self.connect(url, xml)
        if not result:
            return

        dom = parseString(result)

        # Get info
        info = dom.getElementsByTagName('out')
        return info[0].firstChild.data

    def manifiesto(self, data):
        """
            Get Manifiesto

            :param data: Dictionary of values
            :return: string
        """
        tmpl = loader.load('manifiesto.xml')

        vals = {
            'username': self.username,
            'password': self.password,
            'vat': self.vat,
            'franchise': self.franchise_code,
            'seurid': self.seurid,
            'ci': self.integration_code,
            'ccc': self.accounting_code,
        }
        if data.get('date'):
            vals['date'] = data.get('date')
        else:
            d = datetime.now()
            vals['date'] = '%s-%s-%s' % (
                d.year, d.strftime('%m'), d.strftime('%d'))

        url = 'http://cit.seur.com/CIT-war/services/DetalleBultoPDFWebService'
        xml = tmpl.generate(**vals).render()
        result = self.connect(url, xml)
        if not result:
            return

        dom = parseString(result)
        pdf = dom.getElementsByTagName('ns1:out')
        result_pdf = pdf[0].firstChild.data if pdf else None
        try:
            base64.b64decode(result_pdf)
        except TypeError:
            raise UserError(result_pdf)
        return result_pdf

    def get_zip_data(self, zip_code):
        """
            Get Seur values from zip

            :param zip_code: string
            :return: list dict
        """
        tmpl = loader.load('zip.xml')

        vals = {
            'username': self.username,
            'password': self.password,
            'zip': zip_code,
            }

        url = 'https://ws.seur.com/WSEcatalogoPublicos/servlet/XFireServlet' \
            '/WSServiciosWebPublicos'
        xml = tmpl.generate(**vals).render()
        result = self.connect(url, xml)
        if not result:
            return []
        # -_-
        result = result.replace('iso-8859-1', 'UTF-8')
        dom = parseString(result.decode())
        info = dom.getElementsByTagName('ns1:out')
        data = info[0].firstChild.data

        dom2 = parseString(data)
        registros = dom2.getElementsByTagName('REGISTROS')

        total = registros[0].childNodes.length

        values = []
        for i in range(1, total+1):
            reg_name = 'REG%s' % i
            reg = registros[0].getElementsByTagName(reg_name)[0]
            vals = {}
            for r in reg.childNodes:
                vals[r.nodeName] = r.firstChild.data
            values.append(vals)
        return values
