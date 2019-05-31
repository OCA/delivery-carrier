# -*- coding: utf-8 -*-
# This file is part of asm. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from .utils import asm_url
from xml.dom.minidom import parseString
import urllib.request
import requests
import base64
import os
import genshi
import genshi.template
from random import randint

loader = genshi.template.TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'template'),
    auto_reload=True)


class API(object):
    """
    Generic API to connect to ASM
    """
    __slots__ = (
        'url',
        'username',
    )

    def __init__(self, username, debug=False):
        """
        This is the Base API class which other APIs have to subclass. By
        default the inherited classes also get the properties of this
        class which will allow the use of the API with the `with` statement

        Example usage ::

            from asm.api import API

            with API(username) as asm_api:
                return asm_api.test_connection()

        :param username: ASM API username
        """
        self.url = asm_url(debug)
        self.username = username

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def connect(self, xml):
        """
        Connect to the Webservices and return XML data from ASM

        :param xml: XML data.

        Return XML object
        """
        headers = {
            'Content-Type': 'text/xml; charset=utf8',
            }
        request = urllib.request.Request(self.url, xml.encode('utf8'), headers)
        result = urllib.request.urlopen(request)
        return result.read()

    def test_connection(self):
        """
        Test connection to ASM webservices
        Send XML to ASM and return error send data
        """
        tmpl = loader.load('test_connection.xml')

        vals = {
            'referencia_c': randint(1000, 2000),
        }
        xml = tmpl.generate(**vals).render()
        result = self.connect(xml)
        dom = parseString(result)

        Envio = dom.getElementsByTagName('Envio')

        if not Envio:
            return 'Error connection to ASM'

        Errores = Envio[0].getElementsByTagName('Errores')
        if Errores:
            Error = Errores[0].getElementsByTagName('Error')
            if Error:
                error = Error[0].firstChild.data
                return error

        reference = Envio[0].getAttribute('codbarras')
        if reference:
            return 'Succesfully send a test to ASM with tracking "%s"' % (reference)
