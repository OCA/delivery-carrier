# -*- coding: utf-8 -*-
#This file is part of asm. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from .api import API

from xml.dom.minidom import parseString
import os
import datetime
import genshi
import genshi.template

loader = genshi.template.TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'template'),
    auto_reload=True)


class Picking(API):
    """
    Picking API
    """
    __slots__ = ()

    def create(self, data):
        """
        Create delivery to ASM

        :param data: Dict
        :return: reference (str), label(base64), error (str)
        """
        reference = None
        label = None
        error = None

        today = datetime.datetime.now().date()

        tmpl = loader.load('picking_send.xml')
        vals = {
            'username': self.username,
            'today': data.get('today', today),
            'portes': data.get('portes', 'P'),
            'servicio': data.get('servicio', '1'),
            'horario': data.get('horario', '2'),
            'bultos': data.get('bultos', '1'),
            'peso': data.get('peso', '1'),
            'volumen': data.get('volumen', ''),
            'declarado': data.get('declarado', ''),
            'dninob': data.get('dninob', '0'),
            'fechaentrega': data.get('fechaentrega',''),
            'retorno': data.get('retorno', '0'),
            'pod': data.get('pod', 'N'),
            'podobligatorio': data.get('podobligatorio', 'N'),
            'remite_plaza': data.get('remite_plaza', ''),
            'remite_nombre': data.get('remite_nombre'),
            'remite_direccion': data.get('remite_direccion'),
            'remite_poblacion': data.get('remite_poblacion'),
            'remite_provincia': data.get('remite_provincia', ''),
            'remite_pais': data.get('remite_pais'),
            'remite_cp': data.get('remite_cp'),
            'remite_telefono': data.get('remite_telefono', ''),
            'remite_movil': data.get('remite_movil', ''),
            'remite_email': data.get('remite_email',''),
            'remite_departamento': data.get('remite_departamento'),
            'remite_nif': data.get('remite_nif'),
            'remite_observaciones': data.get('remite_observaciones', ''),
            'destinatario_codigo': data.get('destinatario_codigo', ''),
            'destinatario_plaza': data.get('destinatario_plaza',''),
            'destinatario_nombre': data.get('destinatario_nombre'),
            'destinatario_direccion': data.get('destinatario_direccion'),
            'destinatario_poblacion': data.get('destinatario_poblacion'),
            'destinatario_provincia': data.get('destinatario_provincia', ''),
            'destinatario_pais': data.get('destinatario_pais'),
            'destinatario_cp': data.get('destinatario_cp'),
            'destinatario_telefono': data.get('destinatario_telefono', ''),
            'destinatario_movil': data.get('destinatario_movil', ''),
            'destinatario_email': data.get('destinatario_email', ''),
            'destinatario_observaciones': data.get('destinatario_observaciones', ''),
            'destinatario_att': data.get('destinatario_att', ''),
            'destinatario_departamento': data.get('destinatario_departamento', ''),
            'destinatario_nif': data.get('destinatario_nif'),
            'referencia_c': data.get('referencia_c'),
            'referencia_0': data.get('referencia_0'),
            'importes_debido': data.get('importes_debido'),
            'importes_reembolso': data.get('importes_reembolso', '0'),
            'seguro': data.get('seguro', '0'),
            'seguro_descripcion': data.get('seguro_descripcion', ''),
            'seguro_importe': data.get('seguro_importe', ''),
            'etiqueta': data.get('etiqueta', 'PDF'),
            'etiqueta_devolucion': data.get('etiqueta_devolucion', 'PDF'),
            'cliente_codigo': data.get('cliente_codigo', ''),
            'cliente_plaza': data.get('cliente_plaza', ''),
            'cliente_agente': data.get('cliente_agente', ''),
            }
        xml = tmpl.generate(**vals).render()
        result = self.connect(xml)
        dom = parseString(result)

        Envio = dom.getElementsByTagName('Envio')

        Errores = Envio[0].getElementsByTagName('Errores')
        if Errores:
            Error = Errores[0].getElementsByTagName('Error')
            if Error:
                error = Error[0].firstChild.data
                return reference, label, error

        reference = Envio[0].getAttribute('codbarras')

        Etiquetas = Envio[0].getElementsByTagName('Etiquetas')
        if Etiquetas:
            Etiqueta = Etiquetas[0].getElementsByTagName('Etiqueta')
            label = Etiqueta[0].firstChild.data

        return reference, label, error

    def label(self, data):
        """
        Get PDF label from ASM service

        :param data: Dictionary of values
        :return: label (base64)
        """
        label = None

        tmpl = loader.load('picking_label.xml')

        vals = {
            'codigo': data.get('codigo'),
            'tipo_etiqueta': data.get('tipo_etiqueta', 'PDF'), #EPL or DPL or JPG or PNG or PDF
        }
        xml = tmpl.generate(**vals).render()
        result = self.connect(xml)
        dom = parseString(result)

        EtiquetaEnvioResponse = dom.getElementsByTagName('EtiquetaEnvioResponse')
        EtiquetaEnvioResult = EtiquetaEnvioResponse[0].getElementsByTagName('EtiquetaEnvioResult')
        base64Binary = EtiquetaEnvioResult[0].getElementsByTagName('base64Binary')

        label = base64Binary[0].firstChild.data

        return label
