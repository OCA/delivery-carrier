# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import json
import logging
import re

import dicttoxml
import requests
import xmltodict

from odoo import _, fields, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
dicttoxml.LOG.setLevel(logging.ERROR)


class TntRequest(object):
    def __init__(self, carrier, record):
        self.carrier = carrier
        self.record = record
        self.appVersion = 3.0
        self.product_type = self.carrier.tnt_product_type
        self.product_code = self.carrier.tnt_product_code
        self.product_service = self.carrier.tnt_product_service
        self.username = self.carrier.tnt_oca_ws_username
        self.password = self.carrier.tnt_oca_ws_password
        self.account = self.carrier.tnt_oca_ws_account
        self.url = "https://express.tnt.com"
        auth_encoding = "%s:%s" % (self.username, self.password)
        self.authorization = base64.b64encode(auth_encoding.encode("utf-8")).decode(
            "utf-8"
        )

    def _send_api_request(
        self, url, data=None, auth=True, content_type="application/xml"
    ):
        if data is None:
            data = {}
        try:
            headers = {"Content-Type": content_type, "charset": "UTF-8"}
            if auth:
                headers["Authorization"] = "Basic {}".format(self.authorization)
            res = requests.post(
                url=url, data=data.encode("utf-8"), headers=headers, timeout=60
            )
            res.raise_for_status()
            tnt_last_request = ("URL: {}\nData: {}").format(self.url, data)
            self.carrier.log_xml(tnt_last_request, "tnt_last_request")
            self.carrier.log_xml(res.text or "", "tnt_last_response")
            res = res.text
        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 60s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(e, res.json().get("Message", "") if res.text else ""))
            )
        return res

    def _partner_to_shipping_data(self, partner):
        return {
            "country": partner.country_id.code,
            "town": partner.city,
            "postcode": partner.zip,
        }

    def _prepare_product(self):
        return {
            "id": self.product_code,
            "type": self.product_type,
            "options": {"option": {"optionCode": self.product_code}},
        }

    def _prepare_account(self, partner):
        return {
            "accountNumber": self.account,
            "accountCountry": partner.country_id.code,
        }

    def _prepare_rate_shipment(self):
        totalWeight = 0
        totalVolume = 0
        for line in self.record.order_line.filtered(
            lambda x: x.product_id
            and (x.product_id.weight > 0 or x.product_id.volume > 0)
        ):
            totalWeight += line.product_id.weight * line.product_uom_qty
            totalVolume += line.product_id.volume * line.product_uom_qty
        data = {
            "appId": "PC",
            "appVersion": self.appVersion,
            "priceCheck": {
                "rateId": self.record.name,
                "sender": self._partner_to_shipping_data(
                    self.record.company_id.partner_id
                ),
                "delivery": self._partner_to_shipping_data(
                    self.record.partner_shipping_id
                ),
                "collectionDateTime": self.record.expected_date,
                "product": self._prepare_product(),
                "account": self._prepare_account(self.record.company_id.partner_id),
                "currency": self.record.currency_id.name,
                "priceBreakDown": True,
                "consignmentDetails": {
                    "totalWeight": totalWeight,
                    "totalVolume": totalVolume,
                    "totalNumberOfPieces": 1,
                },
            },
        }
        return dicttoxml.dicttoxml(
            data, attr_type=False, custom_root="priceRequest"
        ).decode("utf-8")

    def rate_shipment(self):
        response = self._send_api_request(
            url="%s/expressconnect/pricing/getprice" % self.url,
            data=self._prepare_rate_shipment(),
        )
        response = json.loads(json.dumps(xmltodict.parse(response)))["document"]
        if "errors" in response and "priceResponse" not in response:
            errors = response["errors"]["brokenRule"]
            if type(errors) is not list:
                errors = [errors]
            raise UserError(
                _("Sending to TNT\n%s")
                % ("\n".join("%(code)s %(description)s" % error for error in errors))
            )
        res = {
            "success": False,
            "price": 0,
        }
        if "priceResponse" in response:
            service = response["priceResponse"]["ratedServices"]["ratedService"]
            res["success"] = True
            res["price"] = service["totalPrice"]
            res["currency"] = response["priceResponse"]["ratedServices"]["currency"]
        return res

    # ShippingSevice
    def _quant_package_data_from_picking(self):
        data_total = self._get_data_total_shipping()
        return {
            "ITEMS": self.record.number_of_packages,
            "DESCRIPTION": self.record.name,
            "LENGTH": data_total["length"],
            "HEIGHT": data_total["height"],
            "WIDTH": data_total["width"],
            "WEIGHT": data_total["weight"],
        }

    def _prepare_address(self, partner):
        return {
            "COMPANYNAME": partner.name,
            "STREETADDRESS1": partner.street,
            "CITY": partner.city,
            "PROVINCE": partner.state_id.name,
            "POSTCODE": partner.zip,
            "COUNTRY": partner.country_id.code,
            "ACCOUNT": self.account,
            "VAT": partner.vat or "",
            "CONTACTNAME": partner.name,
            "CONTACTDIALCODE": "0000",
            "CONTACTTELEPHONE": partner.phone,
            "CONTACTEMAIL": partner.email,
        }

    def _prepare_collection(self, partner):
        address = self._prepare_address(partner)
        del address["ACCOUNT"]
        shipdate = self.record.scheduled_date.date()
        return {
            "COLLECTION": {
                "COLLECTIONADDRESS": address,
                "SHIPDATE": "%s/%s/%s" % (shipdate.day, shipdate.month, shipdate.year),
                "PREFCOLLECTTIME": {
                    "FROM": tools.format_duration(self.carrier.tnt_collect_time_from),
                    "TO": tools.format_duration(self.carrier.tnt_collect_time_to),
                },
                "COLLINSTRUCTIONS": "",
            }
        }

    def _prepare_sender(self):
        data = self._prepare_address(self.record.company_id.partner_id)
        collection = self._prepare_collection(self.record.company_id.partner_id)
        data.update(collection)
        return data

    def _get_data_total_shipping(self):
        weight = self.record.shipping_weight
        volume = p_length = height = width = 0
        if self.record.package_ids:
            weight = sum(self.record.package_ids.mapped("quant_ids.quantity"))
            height = max(self.record.package_ids.mapped("height"))
            width = max(self.record.package_ids.mapped("width"))
            p_length = max(self.record.package_ids.mapped("length"))
            for quant in self.record.package_ids.mapped("quant_ids"):
                volume += quant.product_id.volume * quant.quantity
        else:
            lines = self.record.move_line_ids_without_package
            for line in lines.filtered(lambda x: x.qty_done > 0):
                volume += line.product_id.volume * line.qty_done
                p_length += line.product_id.product_length * line.qty_done
                height += line.product_id.product_height * line.qty_done
                width += line.product_id.product_width * line.qty_done
        return {
            "weight": weight,
            "volume": volume,
            "length": p_length,
            "height": height,
            "width": width,
        }

    def _prepare_create_shipping(self):
        receiver = self._prepare_address(self.record.company_id.partner_id)
        del receiver["ACCOUNT"]
        delivery = self._prepare_address(self.record.partner_id)
        del delivery["ACCOUNT"]
        data_total = self._get_data_total_shipping()
        package = self._quant_package_data_from_picking()
        data = {
            "LOGIN": {
                "COMPANY": self.username,
                "PASSWORD": self.password,
                "APPID": "IN",
                "APPVERSION": self.appVersion,
            },
            "CONSIGNMENTBATCH": {
                "SENDER": self._prepare_sender(),
                "CONSIGNMENT": {
                    "CONREF": self.record.name,
                    "DETAILS": {
                        "RECEIVER": receiver,
                        "DELIVERY": delivery,
                        "CUSTOMERREF": self.record.name,
                        "CONTYPE": self.product_type,
                        "PAYMENTIND": self.carrier.tnt_payment_indicator,
                        "ITEMS": self.record.number_of_packages,
                        "TOTALWEIGHT": data_total["weight"],
                        "TOTALVOLUME": data_total["volume"],
                        "SERVICE": self.product_code,
                        "OPTION": "PR",
                        "DESCRIPTION": "",
                        "DELIVERYINST": "",
                        "PACKAGE": package,
                        # Campos no especificados en la documentación pero requeridos
                        "INVOICENUMBER": "",
                        "PURCHASEORDERNUMBER": "",
                        "INCOTERMS": "",
                        "DISCOUNT": "",
                        "INSURANCECHARGES": "",
                        "FREIGHTCHARGES": "",
                        "OTHERCHARGES": "",
                    },
                },
            },
            "ACTIVITY": {
                "CREATE": {"CONREF": self.record.name},
                "BOOK": {"CONREF": self.record.name},
                "SHIP": {"CONREF": self.record.name},
                "PRINT": {
                    "CONNOTE": {"CONREF": self.record.name},
                    "LABEL": {"CONREF": self.record.name},
                    "MANIFEST": {"CONREF": self.record.name},
                },
            },
        }
        xml_info = dicttoxml.dicttoxml(
            data, attr_type=False, custom_root="ESHIPPER"
        ).decode("utf-8")
        return "xml_in=%s" % xml_info

    def _action_picking(self, action, complete_id):
        new_data = "xml_in=%s:%s" % (action, complete_id)
        response = self._send_api_request(
            url="%s/expressconnect/shipping/ship" % self.url,
            data=new_data,
            auth=False,
            content_type="application/x-www-form-urlencoded",
        )
        res = json.loads(json.dumps(xmltodict.parse(response)))
        if "document" in res:
            res = res["document"]
        return res

    def _send_shipping(self):
        response = self._send_api_request(
            url="%s/expressconnect/shipping/ship" % self.url,
            data=self._prepare_create_shipping(),
            auth=False,
            content_type="application/x-www-form-urlencoded",
        )
        complete_id = response.replace("COMPLETE:", "")
        res = self._action_picking("GET_RESULT", complete_id)
        if "ERROR" in res:
            errors = res["ERROR"]
            if type(errors) is not list:
                errors = [errors]
            raise UserError(
                _("Sending to TNT\n%s")
                % ("\n".join("%(CODE)s %(DESCRIPTION)s" % error for error in errors))
            )
        if "CREATE" in res:
            self.record.carrier_tracking_ref = res["CREATE"]["CONNUMBER"]

    # TrackSevice
    def _prepare_state_update(self):
        data = {
            "SearchCriteria": {"ConsignmentNumber": self.record.carrier_tracking_ref},
            "LevelOfDetail": {"Summary": ""},
        }
        xml_info = dicttoxml.dicttoxml(
            data, attr_type=False, custom_root="TrackRequest"
        ).decode("utf-8")
        return "xml_in=%s" % xml_info

    def tracking_state_update(self):
        response = self._send_api_request(
            url="%s/expressconnect/track.do" % self.url,
            data=self._prepare_state_update(),
            content_type="application/x-www-form-urlencoded",
        )
        response = json.loads(json.dumps(xmltodict.parse(response)))
        SummaryCode = response["TrackResponse"]["Consignment"]["SummaryCode"]
        mapped_states = {
            "INT": "in_transit",
            "DEL": "customer_delivered",
            "EXC": "incidence",
            "CNF": "shipping_recorded_in_carrier",
        }
        return {
            "delivery_state": mapped_states.get(SummaryCode, "incidence"),
            "tracking_state_history": SummaryCode,
        }

    # TntLabel
    def _prepare_label_address(self, partner):
        return {
            "name": partner.name,
            "addressLine1": partner.street,
            "town": partner.city,
            "exactMatch": "Y",
            "province": partner.state_id.name,
            "postcode": partner.zip,
            "country": partner.country_id.code,
        }

    def _prepare_label(self):
        data_total = self._get_data_total_shipping()
        data = {
            "consignment": {
                "consignmentIdentity": {
                    "consignmentNumber": re.sub(
                        "[^0-9]", "", self.record.carrier_tracking_ref
                    ),
                    "customerReference": self.record.name,
                },
                "collectionDateTime": fields.Datetime.today(),
                "sender": self._prepare_label_address(
                    self.record.company_id.partner_id
                ),
                "delivery": self._prepare_label_address(self.record.partner_id),
                "product": {
                    "lineOfBusiness": self.record.carrier_id.tnt_line_of_business,
                    "groupId": 0,
                    "subGroupId": 0,
                    "id": self.product_service,
                    "type": self.product_type,
                    "option": self.product_code,
                },
                "account": self._prepare_account(self.record.company_id.partner_id),
                "totalNumberOfPieces": self.record.number_of_packages,
                "pieceLine": {
                    "identifier": 1,
                    "goodsDescription": self.record.name,
                    "pieceMeasurements": {
                        "length": data_total["length"],
                        "width": data_total["width"],
                        "height": data_total["height"],
                        "weight": data_total["weight"],
                    },
                    "pieces": {
                        "sequenceNumbers": self.record.number_of_packages,
                        "pieceReference": "",
                    },
                },
            }
        }
        return dicttoxml.dicttoxml(
            data, attr_type=False, custom_root="labelRequest"
        ).decode("utf-8")

    def _get_label_info(self):
        if not self.record.carrier_tracking_ref:
            return
        response = self._send_api_request(
            url="%s/expresslabel/documentation/getlabel" % self.url,
            data=self._prepare_label(),
            content_type="application/x-www-form-urlencoded",
        )
        res = json.loads(json.dumps(xmltodict.parse(response)))
        if "labelResponse" in res:
            res = res["labelResponse"]
        if "brokenRules" in res:
            errors = res["brokenRules"]
            if type(errors) is not list:
                errors = [errors]
            raise UserError(
                _("Sending to TNT\n%s")
                % (
                    "\n".join(
                        "%(errorCode)s %(errorDescription)s" % error for error in errors
                    )
                )
            )
        res = res["consignment"]
        p_data = res["pieceLabelData"]
        c_data = res["consignmentLabelData"]
        twoDBarcode_text_split = p_data["twoDBarcode"]["#text"].split("|")
        c_data_fcd = c_data["freeCirculationDisplay"]
        c_data_dd = c_data["destinationDepot"]
        vals = {
            "tnt_consignment_mumber": c_data["consignmentNumber"],
            "tnt_consignment_date": twoDBarcode_text_split[-2],
            "tnt_consignment_free_circulation": c_data_fcd["#text"],
            "tnt_consignment_sort_split": c_data["sortSplitText"],
            "tnt_consignment_destination_depot": c_data_dd["depotCode"],
            "tnt_consignment_destination_depot_day": c_data_dd["dueDayOfMonth"],
            "tnt_consignment_cluster_code": c_data["clusterCode"],
            "tnt_consignment_origin_depot": c_data["originDepot"]["depotCode"],
            "tnt_consignment_product": c_data["product"]["#text"],
            "tnt_consignment_option": twoDBarcode_text_split[19],
            "tnt_consignment_market": c_data["marketDisplay"]["#text"],
            "tnt_consignment_transport": c_data["transportDisplay"]["#text"],
            "tnt_piece_barcode": p_data["barcode"]["#text"],
        }
        if "transitDepots" in c_data and c_data["transitDepots"]:
            transitDepot = c_data["transitDepots"]["transitDepot"]
            vals["tnt_consignment_transit_depot"] = transitDepot["depotCode"]
        if "xrayDisplay" in c_data and "#text" in c_data["xrayDisplay"]:
            vals["tnt_consignment_xray"] = c_data["xrayDisplay"]["#text"]
        self.record.write(vals)
