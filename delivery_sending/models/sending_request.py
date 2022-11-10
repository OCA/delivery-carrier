# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2022 Impulso Diagonal - Javier Colmeiro
# Copyright 2022 Tecnativa - Víctor Martínez
import logging

from suds.client import Client
from suds.sax.text import Raw

_logger = logging.getLogger(__name__)


class SendingRequest:
    """Interface between Sending SOAP API and Odoo recordset
       Abstract Sending API Operations to connect them with Odoo
    """

    def __init__(self, uidcustomer, uidpass):
        """As the wsdl isn't public, we have to load it from local"""
        self.uidcustomer = uidcustomer
        self.uidpass = uidpass
        self.url = "http://padua.sending.es/sending/ws_clientes?wsdl"
        self.client = Client(self.url)

    def _prepare_send_shipping_docin(self, **kwargs):
        """Sending is not very standard. Prepare parameters to pass them raw in
           the SOAP message as fichero requires a raw xml string to function"""
        return """<![CDATA[<?xml version="1.0" encoding="ISO-8859-1"?>
            <Expediciones>
              <Expedicion>
                <Fecha>{date}</Fecha>
                <ClienteRemitente>{uidcustomer}</ClienteRemitente>
                <NombreRemitente>{uidcustomername}</NombreRemitente>
                <DireccionRemitente>{uidcustomeraddress}</DireccionRemitente>
                <PaisRemitente>{uidcustomercountry}</PaisRemitente>
                <CodigoPostalRemitente>{uidcustomerzip}</CodigoPostalRemitente>
                <PoblacionRemitente>{uidcustomercity}</PoblacionRemitente>
                <NombreDestinatario>{clientname}</NombreDestinatario>
                <DireccionDestinatario>{clientaddress}</DireccionDestinatario>
                <PaisDestinatario>{clientcountry}</PaisDestinatario>
                <CodigoPostalDestinatario>{clientzip}</CodigoPostalDestinatario>
                <PoblacionDestinatario>{clientcity}</PoblacionDestinatario>
                <PersonaContactoDestinatario>{clientcontact}</PersonaContactoDestinatario>
                <TelefonoContactoDestinatario>{clientphone}</TelefonoContactoDestinatario>
                <EnviarMail>N</EnviarMail>
                <MailDestinatario></MailDestinatario>
                <ProductoServicio>{service}</ProductoServicio>
                <Observaciones1>{note}</Observaciones1>
                <Kilos>{weight}</Kilos>
                <Volumen>0.00</Volumen>
                <ReferenciaCliente>{ref}</ReferenciaCliente>
                <TipoPortes>P</TipoPortes>
                <EntregaSabado>N</EntregaSabado>
                <Retorno>N</Retorno>
                <Bultos>{number_of_packages}</Bultos>
              </Expedicion>
            </Expediciones>]]>""".format(
            **kwargs
        )

    def send_shipping(self, vals):
        """Create new shipment"""
        vals.update({"uidcustomer": self.uidcustomer, "uidpass": self.uidpass})
        data = self._prepare_send_shipping_docin(**vals)
        return self.client.service.entrada_expediciones(
            cliente=self.uidcustomer,
            formato="xml",
            param1=self.uidpass,
            fichero=Raw(data),
        )

    def _shipping_label_zpl(self, reference):
        """Get shipping label ZPL for the given ref
        :param reference -- shipping reference
        :returns: base64 with pdf labels
        """
        return self.client.service.etiquetarExpedicionZPL(
            cliente=self.uidcustomer, expedicion=reference
        )

    def _shipping_label_pdf(self, reference):
        """Get shipping label PDF for the given ref
        :param reference -- shipping reference
        :returns: base64 with pdf labels
        """
        return self.client.service.etiquetarExpedicionPDF(
            cliente=self.uidcustomer,
            expedicion=reference,
            usuario=self.uidcustomer,
            param1=self.uidpass,
        )

    def _cancel_shipment(self, reference=False):
        """Cancel shipment for a given reference"""
        return self.client.service.cancelarExpedicion(
            cliente=self.uidcustomer, param1=self.uidpass, expedicion=reference
        )
