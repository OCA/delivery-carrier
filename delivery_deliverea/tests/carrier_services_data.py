CARRIER_LIST = {
    "data": [
        {
            "distributionCenterId": "d19f3f7b-6c53-4a0d-940f-0003b8bea864",
            "code": "dhl",
            "costCenters": [
                {
                    "code": "DEFAULT",
                    "active": True,
                    "services": [
                        {"code": "day-definite-eu", "active": True},
                        {"code": "day-definite-intl", "active": True},
                        {"code": "time-definite-canarias", "active": True},
                        {"code": "time-definite-eu", "active": True},
                        {"code": "time-definite-intl", "active": True},
                        {"code": "time-definite-national", "active": False},
                    ],
                }
            ],
        },
        {
            "distributionCenterId": "d19f3f7b-6c53-4a0d-940f-0003b8bea864",
            "code": "gls",
            "costCenters": [
                {
                    "code": "DEFAULT",
                    "active": True,
                    "services": [
                        {"code": "gls-830", "active": True},
                        {"code": "gls-courier-10", "active": True},
                        {"code": "gls-courier-14", "active": True},
                        {"code": "gls-courier-24", "active": True},
                        {"code": "gls-economy", "active": True},
                        {"code": "gls-euro-business-parcel", "active": True},
                        {"code": "gls-maritimo", "active": False},
                    ],
                }
            ],
        },
        {
            "distributionCenterId": "d19f3f7b-6c53-4a0d-940f-0003b8bea864",
            "code": "tipsa",
            "costCenters": [
                {
                    "code": "DEFAULT",
                    "active": True,
                    "services": [
                        {"code": "tipsa-10-horas", "active": True},
                        {"code": "tipsa-14-horas", "active": True},
                        {"code": "tipsa-baleares", "active": True},
                        {"code": "tipsa-canarias", "active": True},
                        {"code": "tipsa-economy", "active": True},
                        {"code": "tipsa-masivo", "active": True},
                    ],
                }
            ],
        },
    ],
}

DHL_DETAILS = {
    "active": True,
    "code": "DEFAULT",
    "contact": "",
    "credentials": {
        "account_number": "*****",
        "code_client": "DELIVEREA",
        "import_account_number": "*****",
        "password": "*****",
    },
    "integrationCode": "any-v1",
    "labelRangeId": "",
    "labelSource": "carrier",
    "labelType": "zpl",
    "needsPreDraft": True,
    "services": [
        {
            "active": True,
            "code": "day-definite-eu",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "day-definite-intl",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "time-definite-canarias",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "time-definite-eu",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "time-definite-intl",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": False,
            "code": "time-definite-national",
            "expirationTime": {"time": 15, "unit": "days"},
        },
    ],
}


DHL_SERVICES = {
    "code": "any-v1",
    "carrierCode": "dhl",
    "supportedCountries": ["ANY"],
    "services": [
        {
            "code": "time-definite-national",
            "name": "Time Definite - Nacional",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "time-definite-eu",
            "name": "Time Definite - Union Europea",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "time-definite-intl",
            "name": "Time Definite - Internacional",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "day-definite-eu",
            "name": "Day Definite - Union Europea",
            "description": "",
            "type": "72",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "day-definite-intl",
            "name": "Day Definite - Internacional",
            "description": "",
            "type": "72",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "time-definite-canarias",
            "name": "Time Definite - Canarias",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
    ],
    "supportedFeatures": ["documentExpedition", "getProofOfDelivery", "getLabel"],
    "supportedLabels": [{"source": "carrier", "types": ["pdf"]}],
    "credentialsFields": [
        {"key": "code_client", "label": "Id Cliente"},
        {"key": "password", "label": "Contraseña"},
        {"key": "account_number", "label": "Código de cuenta para exportaciones"},
        {
            "key": "import_account_number",
            "label": "Código de cuenta para importaciones",
        },
    ],
}

GLS_DETAILS = {
    "active": True,
    "code": "DEFAULT",
    "contact": "",
    "credentials": {"UIDClient": "6BAB7A53-3B6D-4D5A-9450-702D2FAC0B11"},
    "integrationCode": "es-v1",
    "labelRangeId": "",
    "labelSource": "carrier",
    "labelType": "zpl",
    "needsPreDraft": True,
    "services": [
        {
            "active": True,
            "code": "gls-830",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "gls-courier-10",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "gls-courier-14",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "gls-courier-24",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "gls-economy",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "gls-euro-business-parcel",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": False,
            "code": "gls-maritimo",
            "expirationTime": {"time": 15, "unit": "days"},
        },
    ],
}

GLS_SERVICES = {
    "code": "es-v1",
    "carrierCode": "gls",
    "supportedCountries": ["ES"],
    "services": [
        {
            "code": "gls-courier-10",
            "name": "COURIER entrega antes de las 10:00 ",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "gls-courier-14",
            "name": "COURIER entrega antes de las 14:00",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "gls-courier-24",
            "name": "COURIER entrega antes de las 20:00",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "gls-economy",
            "name": "ECONOMY",
            "description": "",
            "type": "72",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "gls-830",
            "name": "Entrega a primera hora de la mañana",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "gls-euro-business-parcel",
            "name": "EUROBUSINESS SMALL PARCEL",
            "description": "Este servicio solo acepta envíos monobulto",
            "type": "72",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "gls-maritimo",
            "name": "MARÍTIMO",
            "description": "",
            "type": "72",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
    ],
    "supportedFeatures": ["documentExpedition", "getLabel"],
    "supportedLabels": [
        {"source": "carrier", "types": ["pdf"]},
        {"source": "label-engine", "types": ["pdf"]},
    ],
    "credentialsFields": [{"key": "UIDClient", "label": "Id de cliente"}],
}

TIPSA_DETAILS = {
    "active": True,
    "code": "DEFAULT",
    "contact": "",
    "credentials": {
        "code_agency": "000000",
        "code_client": "33333",
        "pwd": "PR%20%18%",
    },
    "integrationCode": "es-v1",
    "labelRangeId": "",
    "labelSource": "carrier",
    "labelType": "zpl",
    "needsPreDraft": True,
    "services": [
        {
            "active": True,
            "code": "tipsa-10-horas",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "tipsa-14-horas",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "tipsa-baleares",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "tipsa-canarias",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "tipsa-economy",
            "expirationTime": {"time": 15, "unit": "days"},
        },
        {
            "active": True,
            "code": "tipsa-masivo",
            "expirationTime": {"time": 15, "unit": "days"},
        },
    ],
}

TIPSA_SERVICES = {
    "code": "es-v1",
    "carrierCode": "tipsa",
    "supportedCountries": ["ES"],
    "services": [
        {
            "code": "tipsa-10-horas",
            "name": "Urgente 10 horas",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "tipsa-14-horas",
            "name": "Urgente 14 Horas",
            "description": "",
            "type": "24",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "tipsa-economy",
            "name": "Economy",
            "description": "",
            "type": "48",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "tipsa-masivo",
            "name": "Masivo 48/72 Horas",
            "description": "",
            "type": "72",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "tipsa-baleares",
            "name": "Baleares Area/Maritima",
            "description": "",
            "type": "48",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
        {
            "code": "tipsa-canarias",
            "name": "Canarias Maritima",
            "description": "",
            "type": "72",
            "parameters": [
                {
                    "name": "senderGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientGeolocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "cashOnDelivery",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "dropPointKey",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "pickupTime",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "deliveryTime",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "notificationViaSMS",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "notificationViaEmail",
                    "necessity": {"type": "optional", "condition": None},
                },
                {
                    "name": "saturdayDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "includeReturnLabel",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "insuranceValue",
                    "necessity": {"type": "unsupported", "condition": None},
                },
                {
                    "name": "maxShippingDays",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "returnProofOfDelivery",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "hideSender",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "containerNumber",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermLocation",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "incotermZipCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "senderStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "recipientStateCode",
                    "necessity": {"type": "ignored", "condition": None},
                },
                {
                    "name": "parcelLabelBarcode",
                    "necessity": {"type": "ignored", "condition": None},
                },
            ],
        },
    ],
    "supportedFeatures": [
        "documentExpedition",
        "cancelExpedition",
        "getLabel",
        "getProofOfDelivery",
        "labellessPickup",
    ],
    "supportedLabels": [{"source": "carrier", "types": ["pdf"]}],
    "credentialsFields": [
        {"key": "code_agency", "label": "Código de agencia"},
        {"key": "code_client", "label": "Id de cliente"},
        {"key": "pwd", "label": "Contraseña"},
    ],
}
