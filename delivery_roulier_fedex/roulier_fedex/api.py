#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from roulier.api import ApiParcel, BaseApi

from .constants import LABEL_FORMATS, LENGTH_UNITS, PAYMENT_TYPES, WEIGHT_UNITS

REQUIRED_STRING = {"type": "string", "required": True, "empty": False}


def _fedex_auth(schema):
    schema["login"].update({"required": True, "empty": False})
    schema["password"].update({"required": True, "empty": False})
    return schema


class FedexApiParcel(ApiParcel):
    def _auth(self):
        return _fedex_auth(super()._auth())

    def _address(self):
        schema = super()._address()
        schema["phone"].update({"required": True, "empty": False})
        schema.update(
            {
                "street3": {"type": "string", "default": ""},
                "state": {"type": "string", "default": ""},
                "residential": {"type": "boolean", "default": False},
            }
        )
        return schema

    def _from_address(self):
        schema = super()._from_address()
        for field in ("street1", "city", "zip", "country"):
            schema[field].update({"required": True, "empty": False})
        return schema

    def _service(self):
        schema = super()._service()
        schema["product"].update(REQUIRED_STRING)
        schema["labelFormat"].update(
            {"type": "string", "default": "PDF", "allowed": LABEL_FORMATS}
        )
        schema.update(
            {
                "accountNumber": dict(REQUIRED_STRING),
                "labelStockType": {"type": "string", "default": "PAPER_4X6"},
                "pickupType": {"type": "string", "default": "USE_SCHEDULED_PICKUP"},
                "packagingType": {"type": "string", "default": "YOUR_PACKAGING"},
                "paymentType": {
                    "type": "string",
                    "default": "SENDER",
                    "allowed": PAYMENT_TYPES,
                },
                "etd": {"type": "boolean", "default": False},
            }
        )
        return schema

    def _parcel(self):
        schema = super()._parcel()
        schema["weight"].update({"min": 0.01})
        schema.update(
            {
                "weightUnit": {
                    "type": "string",
                    "default": "KG",
                    "allowed": WEIGHT_UNITS,
                },
                "dimensions": {
                    "type": "dict",
                    "required": False,
                    "schema": {
                        "length": {"type": "integer", "required": True, "min": 1},
                        "width": {"type": "integer", "required": True, "min": 1},
                        "height": {"type": "integer", "required": True, "min": 1},
                        "unit": {
                            "type": "string",
                            "default": "CM",
                            "allowed": LENGTH_UNITS,
                        },
                    },
                },
            }
        )
        return schema

    def _commodity(self):
        return {
            "description": dict(REQUIRED_STRING),
            "quantity": {"type": "integer", "required": True, "min": 1},
            "unitPrice": {"type": "float", "required": True},
            "weight": {"type": "float", "required": True},
            "countryOfManufacture": dict(REQUIRED_STRING),
            "harmonizedCode": {"type": "string", "default": ""},
        }

    def _customs(self):
        return {
            "type": "dict",
            "required": False,
            "schema": {
                "currency": dict(REQUIRED_STRING),
                "weightUnit": {
                    "type": "string",
                    "default": "KG",
                    "allowed": WEIGHT_UNITS,
                },
                "dutiesPaymentType": {
                    "type": "string",
                    "default": "SENDER",
                    "allowed": PAYMENT_TYPES,
                },
                "shipmentPurpose": {"type": "string", "default": "SOLD"},
                "incoterm": {"type": "string", "default": ""},
                "commodities": {
                    "type": "list",
                    "required": True,
                    "empty": False,
                    "schema": {"type": "dict", "schema": self._commodity()},
                },
            },
        }

    def _schemas(self):
        schemas = super()._schemas()
        schemas["customs"] = self._customs()
        return schemas


class FedexApiCancel(BaseApi):
    def _auth(self):
        return _fedex_auth(super()._auth())

    def _schemas(self):
        return {
            "auth": self._auth(),
            "shipment": {
                "accountNumber": dict(REQUIRED_STRING),
                "trackingNumber": dict(REQUIRED_STRING),
            },
        }
