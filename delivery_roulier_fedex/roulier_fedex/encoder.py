#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from roulier.codec import Encoder

from .constants import (
    CITY_SIZE,
    COMMODITY_DESCRIPTION_SIZE,
    COMPANY_NAME_SIZE,
    CUSTOMER_REFERENCE_SIZE,
    MAX_STREET_LINES,
    PERSON_NAME_SIZE,
    PHONE_SIZE,
    STREET_LINE_SIZE,
)


class FedexEncoder(Encoder):
    def transform_input_to_carrier_webservice(self, data):
        service = data["service"]
        parcels = data["parcels"]
        requested_shipment = {
            "shipDatestamp": service["shippingDate"].isoformat(),
            "serviceType": service["product"],
            "packagingType": service["packagingType"],
            "pickupType": service["pickupType"],
            "shipper": self._transform_party(data["from_address"]),
            "recipients": [self._transform_party(data["to_address"])],
            "shippingChargesPayment": self._transform_payment(service),
            "labelSpecification": {
                "imageType": service["labelFormat"],
                "labelStockType": service["labelStockType"],
            },
            "totalPackageCount": len(parcels),
            "requestedPackageLineItems": [
                self._transform_parcel(parcel, sequence, service)
                for sequence, parcel in enumerate(parcels, start=1)
            ],
        }
        if data.get("customs"):
            requested_shipment["customsClearanceDetail"] = self._transform_customs(
                data["customs"]
            )
            if service["etd"]:
                requested_shipment.update(self._transform_etd())
        body = {
            "labelResponseOptions": "LABEL",
            "accountNumber": {"value": service["accountNumber"]},
            "requestedShipment": requested_shipment,
        }
        return {"body": body, "auth": data["auth"]}

    def _transform_party(self, address):
        contact = {
            "personName": address["name"][:PERSON_NAME_SIZE],
            "phoneNumber": address["phone"][:PHONE_SIZE],
        }
        if address.get("company"):
            contact["companyName"] = address["company"][:COMPANY_NAME_SIZE]
        if address.get("email"):
            contact["emailAddress"] = address["email"]
        street_lines = [
            address[field][:STREET_LINE_SIZE]
            for field in ("street1", "street2", "street3")
            if address.get(field)
        ]
        fedex_address = {
            "streetLines": street_lines[:MAX_STREET_LINES],
            "city": address["city"][:CITY_SIZE],
            "postalCode": address["zip"],
            "countryCode": address["country"].upper(),
        }
        if address.get("state"):
            fedex_address["stateOrProvinceCode"] = address["state"]
        if address.get("residential"):
            fedex_address["residential"] = True
        return {"contact": contact, "address": fedex_address}

    def _transform_payment(self, service):
        payment = {"paymentType": service["paymentType"]}
        if service["paymentType"] == "SENDER":
            payment["payor"] = {
                "responsibleParty": {
                    "accountNumber": {"value": service["accountNumber"]},
                }
            }
        return payment

    def _transform_parcel(self, parcel, sequence, service):
        package = {
            "sequenceNumber": sequence,
            "weight": {
                "units": parcel["weightUnit"],
                "value": round(parcel["weight"], 2),
            },
        }
        if parcel.get("dimensions"):
            dimensions = parcel["dimensions"]
            package["dimensions"] = {
                "length": dimensions["length"],
                "width": dimensions["width"],
                "height": dimensions["height"],
                "units": dimensions["unit"],
            }
        references = [
            ("CUSTOMER_REFERENCE", service.get("reference1")),
            ("P_O_NUMBER", service.get("reference2")),
            ("INVOICE_NUMBER", service.get("reference3")),
        ]
        customer_references = [
            {
                "customerReferenceType": reference_type,
                "value": value[:CUSTOMER_REFERENCE_SIZE],
            }
            for reference_type, value in references
            if value
        ]
        if customer_references:
            package["customerReferences"] = customer_references
        return package

    def _transform_customs(self, customs):
        currency = customs["currency"]
        commodities = [
            self._transform_commodity(commodity, currency, customs["weightUnit"])
            for commodity in customs["commodities"]
        ]
        commercial_invoice = {"shipmentPurpose": customs["shipmentPurpose"]}
        if customs.get("incoterm"):
            commercial_invoice["termsOfSale"] = customs["incoterm"]
        return {
            "dutiesPayment": {"paymentType": customs["dutiesPaymentType"]},
            "isDocumentOnly": False,
            "commercialInvoice": commercial_invoice,
            "totalCustomsValue": {
                "amount": round(
                    sum(c["customsValue"]["amount"] for c in commodities), 2
                ),
                "currency": currency,
            },
            "commodities": commodities,
        }

    def _transform_commodity(self, commodity, currency, weight_unit):
        fedex_commodity = {
            "description": commodity["description"][:COMMODITY_DESCRIPTION_SIZE],
            "countryOfManufacture": commodity["countryOfManufacture"].upper(),
            "quantity": commodity["quantity"],
            "quantityUnits": "PCS",
            "numberOfPieces": 1,
            "unitPrice": {
                "amount": round(commodity["unitPrice"], 2),
                "currency": currency,
            },
            "customsValue": {
                "amount": round(commodity["unitPrice"] * commodity["quantity"], 2),
                "currency": currency,
            },
            "weight": {
                "units": weight_unit,
                "value": round(commodity["weight"], 2),
            },
        }
        if commodity.get("harmonizedCode"):
            fedex_commodity["harmonizedCode"] = commodity["harmonizedCode"]
        return fedex_commodity

    def _transform_etd(self):
        return {
            "shipmentSpecialServices": {
                "specialServiceTypes": ["ELECTRONIC_TRADE_DOCUMENTS"],
                "etdDetail": {"requestedDocumentTypes": ["COMMERCIAL_INVOICE"]},
            },
            "shippingDocumentSpecification": {
                "shippingDocumentTypes": ["COMMERCIAL_INVOICE"],
                "commercialInvoiceDetail": {
                    "documentFormat": {"stockType": "PAPER_LETTER", "docType": "PDF"}
                },
            },
        }


class FedexCancelEncoder(Encoder):
    def transform_input_to_carrier_webservice(self, data):
        shipment = data["shipment"]
        body = {
            "accountNumber": {"value": shipment["accountNumber"]},
            "trackingNumber": shipment["trackingNumber"],
            "deletionControl": "DELETE_ALL_PACKAGES",
        }
        return {"body": body, "auth": data["auth"]}
