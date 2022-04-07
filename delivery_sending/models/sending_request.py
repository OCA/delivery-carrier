# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from suds.client import Client
    from suds.sax.text import Raw
    from suds.plugin import MessagePlugin
except (ImportError, IOError) as err:
    _logger.debug(err)


class LogPlugin(MessagePlugin):
    def sending(self, context):
        print(str(context.envelope))

    def received(self, context):
        print(str(context.reply))


class SendingRequest:
    """Interface between Sending SOAP API and Odoo recordset
       Abstract Sending API Operations to connect them with Odoo
    """

    def __init__(self, uidcustomer=None, uidpass=None):
        """As the wsdl isn't public, we have to load it from local"""
        print("ENTRO INIT SENDING")
        wsdl_url = "http://padua.sending.es/sending/ws_clientes?wsdl"
        self.uidcustomer = uidcustomer or ""
        self.uidpass = uidpass or ""
        self.client = Client(wsdl_url, plugins=[LogPlugin()])

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

    def _send_shipping(self, vals):
        """Create new shipment
        """
        print("ENTRO _SEND_SHIPPING")
        vals.update({"uidcustomer": self.uidcustomer, "uidpass": self.uidpass})
        fichero = Raw(self._prepare_send_shipping_docin(**vals))
        _logger.debug(fichero)
        print(fichero)
        try:
            res = self.client.service.entrada_expediciones(
                cliente=self.uidcustomer,
                formato="xml",
                param1=self.uidpass,
                fichero=fichero,
            )
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording Sending delivery {}.\n"
                    "Traceback:\n{}"
                ).format(vals.get("ref", ""), e)
            )

        if res[:2] != "OK" and res[:2] != "TE":
            raise UserError(
                _(
                    "Sending returned an error trying to record the shipping for {}.\n"
                    "Error:\n{}"
                ).format(vals.get("ref", ""), res)
            )
        # todo get label
        print(res)
        return res

    def _shipping_label_zpl(self, reference):
        """Get shipping label ZPL for the given ref
        :param reference -- shipping reference
        :returns: base64 with pdf labels
        """
        try:
            res = self.client.service.etiquetarExpedicionZPL(
                cliente=self.uidcustomer, expedicion=reference
            )
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording Sending delivery {}.\n"
                    "Traceback:\n{}"
                ).format(vals.get("ref", ""), e)
            )
        return res

    def _shipping_label_pdf(self, reference):
        """Get shipping label PDF for the given ref
        :param reference -- shipping reference
        :returns: base64 with pdf labels
        """
        try:
            res = self.client.service.etiquetarExpedicionPDF(
                cliente=self.uidcustomer,
                expedicion=reference,
                usuario=self.uidcustomer,
                param1=self.uidpass,
            )
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording Sending delivery {}.\n"
                    "Traceback:\n{}"
                ).format(vals.get("ref", ""), e)
            )
        return res

    def _cancel_shipment(self, reference=False):
        """Cancel shipment for a given reference
        """
        try:
            response = self.client.service.cancelarExpedicion(
                cliente=self.uidcustomer, param1=self.uidpass, expedicion=reference
            )
            _logger.debug(response)
        except Exception as e:
            _logger.error(
                "No response from server canceling Sending ref {}.\n"
                "Traceback:\n{}".format(reference, e)
            )
            return {}
        print(response)
        return response
