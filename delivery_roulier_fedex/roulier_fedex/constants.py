#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

CARRIER_TYPE = "fedex_rest"

PRODUCTION_URL = "https://apis.fedex.com"
SANDBOX_URL = "https://apis-sandbox.fedex.com"

TOKEN_ENDPOINT = "/oauth/token"
SHIP_ENDPOINT = "/ship/v1/shipments"
CANCEL_ENDPOINT = "/ship/v1/shipments/cancel"

REQUEST_TIMEOUT = 60
TOKEN_EXPIRY_MARGIN = 120

LABEL_FORMATS = ("PDF", "ZPLII", "PNG")
WEIGHT_UNITS = ("KG", "LB")
LENGTH_UNITS = ("CM", "IN")
PAYMENT_TYPES = ("SENDER", "RECIPIENT", "THIRD_PARTY")

MAX_STREET_LINES = 3
STREET_LINE_SIZE = 35
PERSON_NAME_SIZE = 70
COMPANY_NAME_SIZE = 35
CITY_SIZE = 35
PHONE_SIZE = 15
CUSTOMER_REFERENCE_SIZE = 30
COMMODITY_DESCRIPTION_SIZE = 450
