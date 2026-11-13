# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# Master Data provided by Dachser (Codelist V4.0.2 & REST API v2)

DACHSER_DEFAULT_API_URL = "https://api-gateway.dachser.com/rest/v2"
DACHSER_DEFAULT_BASE_URL = DACHSER_DEFAULT_API_URL

DACHSER_TRACKING_BASE_URL = "https://elogistics.dachser.com/shpdl/"
DACHSER_TRACKING_URL_TEMPLATE = (
    "https://elogistics.dachser.com/shpdl/?l={lang}&c=10&n={tracking_ref}"
)

DACHSER_OPERATION_MODES = [
    ("transportorder", "Full Transport Order (/rest/v2/transportorders)"),
    ("label_only", "SSCC Labels + LDR Routing Only (/rest/v2/labels)"),
]

DACHSER_BASKETS = [
    ("imported", "Imported (Draft in eLogistics without label)"),
    ("labelled", "Labelled (Generate SSCC labels; confirm shipment later)"),
    ("sent", "Sent (Generate SSCC labels and transmit to TMS immediately)"),
]

DACHSER_DIVISIONS = [
    ("T", "(T) European Logistics"),
    ("F", "(F) Food Logistics"),
]

DACHSER_PRODUCTS_T = [
    ("Z", "(Z) targospeed"),
    ("S", "(S) targospeed 10"),
    ("E", "(E) targospeed 12"),
    ("X", "(X) targospeed plus"),
    ("V", "(V) targofix"),
    ("R", "(R) targofix 10"),
    ("W", "(W) targofix 12"),
    ("Y", "(Y) targoflex"),
    ("A", "(A) targo on-site *"),
    ("B", "(B) targo on-site plus *"),
    ("H", "(H) targo on-site premium"),
    ("N", "(N) classicline"),
    ("U", "(U) targo on-site fix **"),
    ("custom", "Custom Product Code"),
]

DACHSER_PRODUCTS_F = [
    ("E", "(E) vengospeed"),
    ("S", "(S) vengospeed 11"),
    ("N", "(N) vengoflex"),
    ("K", "(K) vengoflex"),
    ("Q", "(Q) vengofix"),
    ("X", "(X) vengospeed plus"),
    ("I", "(I) weekend service"),
    ("L", "(L) weekend service 11"),
    ("custom", "Custom Product Code"),
]

# Unified product selection for both divisions (T & F)
DACHSER_PRODUCTS = [
    ("Y", "Y - targoflex / vengoflex (Standard Flexible)"),
    ("Z", "Z - targospeed (Priority Express)"),
    ("X", "X - targospeed plus / vengospeed plus"),
    ("S", "S - targospeed 10 / vengospeed 11"),
    ("E", "E - targospeed 12 / vengospeed"),
    ("V", "V - targofix (Fixed Delivery Date)"),
    ("R", "R - targofix 10"),
    ("W", "W - targofix 12"),
    ("Q", "Q - vengofix"),
    ("N", "N - classicline / vengoflex"),
    ("A", "A - targo on-site *"),
    ("B", "B - targo on-site plus *"),
    ("H", "H - targo on-site premium"),
    ("U", "U - targo on-site fix **"),
    ("K", "K - vengoflex"),
    ("I", "I - weekend service"),
    ("L", "L - weekend service 11"),
    ("T", "T - targofix 12"),
    ("C", "C - targo on-site fix"),
    ("custom", "Custom Product Code"),
]

DACHSER_FIXED_DATE_PRODUCTS = {"V", "R", "W", "Q", "U", "T", "C", "X"}

DACHSER_TERMS = [
    ("011", "(011) Ex works"),
    ("021", "(021) Ex works / Freight collect (EXW)"),
    ("023", "(023) Free carrier (FCA)"),
    ("026", "(026) Freight paid to border"),
    ("031", "(031) Free delivered"),
    ("035", "(035) Ex works including delivery against invoice "),
    ("036", "(036) Carriage and insurance paid (CPT / CIP)"),
    ("041", "(041) Free border; uncleared excluding duty & tax"),
    ("051", "(051) Free border / DDU"),
    ("081", "(081) Free delivered; uncleared excluding duty & tax"),
    ("082", "(082) Free delivered; cleared excluding duty & tax"),
    ("083", "(083) Free delivered; cleared including duty, excluding tax"),
    ("084", "(084) Free delivered; cleared including duty & tax"),
    ("085", "(085) Free delivered; insured, uncleared, excluding duty & tax"),
    ("091", "(091) DDP (Delivered Duty Paid)"),
    ("995", "(995) Service goods, insured; only by arrangement with the consolidator"),
    ("custom", "Custom Delivery Term Code"),
]

# Mapping from standard Incoterm codes to Dachser Delivery Term codes
DACHSER_INCOTERM_TO_TERM = {
    "EXW": "021",
    "FCA": "023",
    "FAS": "011",
    "FOB": "011",
    "CPT": "036",
    "CIP": "036",
    "CFR": "031",
    "CIF": "031",
    "DAP": "031",
    "DPU": "031",
    "DDP": "091",
}
INCOTERM_TO_DACHSER_TERM = DACHSER_INCOTERM_TO_TERM

DACHSER_PACKAGING_T = [
    ("LP", "(LP) large packaging"),
    ("DG", "(DG) pressure receptacle"),
    ("GE", "(GE) receptacle"),
    ("S", "(S) Bag"),
    ("SA", "(SA) Bag / Sack"),
    ("BL", "(BL) Bale"),
    ("BR", "(BR) Barrel"),
    ("FA", "(FA) Barrel / Drum"),
    ("PT", "(PT) Batch"),
    ("BB", "(BB) Big Bag"),
    ("FL", "(FL) Bottle"),
    ("BX", "(BX) Box"),
    ("E", "(E) Bucket"),
    ("B", "(B) Bundle"),
    ("BD", "(BD) Bundle"),
    ("KT", "(KT) Carton"),
    ("RO", "(RO) Castor"),
    ("C2", "(C2) Chep-Half-Pallet"),
    ("C0", "(C0) Chep-Industrial Pallet 1,2x1m"),
    ("C4", "(C4) Chep-Quarter-Pallet"),
    ("C1", "(C1) Chep-Standard-Pallet"),
    ("CC", "(CC) Collapsable Stillage"),
    ("CT", "(CT) Container"),
    ("CO", "(CO) Container"),
    ("CR", "(CR) Crate"),
    ("KI", "(KI) Wooden Crate (Case)"),
    ("KH", "(KH) Customer Sterile Pallet"),
    ("ZK", "(ZK) Customs envelope"),
    ("DI", "(D) Display"),
    ("EW", "(EW) Disposable Pallet"),
    ("PX", "(PX) Disposable / One-Way Pallet"),
    ("F", "(F) Drum"),
    ("DD", "(DD) Düsseldorfer pallet"),
    ("EP", "(EP) Dusseldorf Half Pallet (80 x 60 cm)"),
    ("M1", "(M1) Euro container 150mm"),
    ("M2", "(M2) Euro container 220mm"),
    ("M3", "(M3) Euro container 300mm"),
    ("EU", "(EU) Euro Pallet"),
    ("E2", "(E2) Euro-Meat-Tray 2"),
    ("AR", "(AR) Frame"),
    ("HE", "(HE) Half EU pallet"),
    ("HP", "(HP) Half Pallet"),
    ("IP", "(IP) Industrial Pallet"),
    ("IB", "(IB) Intermediate bulk container"),
    ("I1", "(I1) IPP Euro pallet"),
    ("I2", "(I2) I2 IPP half pallet"),
    ("I4", "(I4) I4 IPP quarter pallet"),
    ("KN", "(KN) Jerrican"),
    ("FB", "(FB) Light gauge metal packaging"),
    ("PA", "(PA) Parcel/Packet"),
    ("ST", "(ST) Piece"),
    ("KK", "(KK) Plastic jerrican"),
    ("KD", "(KD) Plastic DD pal (customer own)"),
    ("PH", "(PH) Privately-owned Container"),
    ("SD", "(SD) Protection lid"),
    ("VE", "(VE) Quarter EU-pallet"),
    ("G", "(G) Rack"),
    ("RL", "(RL) Roll"),
    ("RC", "(RC) Roll&GOH"),
    ("VG", "(VG) Security cage"),
    ("GB", "(GB) Skeleton box pallet"),
    ("TR", "(TR) Spool"),
    ("H1", "(H1) Sterile Pallet 1"),
]

DACHSER_PACKAGING_F = [
    ("BL", "(BL) Bale"),
    ("PT", "(PT) Batch"),
    ("BB", "(BB) Big Bag"),
    ("FL", "(FL) Bottle"),
    ("BX", "(BX) Box"),
    ("E", "(E) Bucket"),
    ("KT", "(KT) Carton"),
    ("RO", "(RO) Castor"),
    ("C2", "(C2) Chep-Half-Pallet"),
    ("C4", "(C4) Chep-Quarter-Pallet"),
    ("C1", "(C1) Chep-Standard-Pallet"),
    ("CC", "(CC) Collapsable Stillage"),
    ("CT", "(CT) Container"),
    ("KE", "(KE) Customer Euro- Meat Tray 2"),
    ("KH", "(KH) Customer Sterile Pallet"),
    ("DI", "(DI) Display"),
    ("EW", "(EW) Disposable Pallet"),
    ("PX", "(PX) Disposable / One-Way Pallet"),
    ("F", "(F) Drum"),
    ("DD", "(DD) Düsseldorfer pallet"),
    ("EP", "(EP) Dusseldorf Half Pallet (80 x 60 cm)"),
    ("HP", "(HP) Half Pallet"),
    ("B1", "(B1) E-performance case 1"),
    ("B2", "(B2) E-performance case 2"),
    ("B3", "(B3) E-performance case 3"),
    ("M1", "(M1) Euro container 150mm"),
    ("M2", "(M2) Euro container 220mm"),
    ("M3", "(M3) Euro container 300mm"),
    ("EU", "(EU) Euro Pallet"),
    ("E1", "(E1) Euro-Meat-Tray 1"),
    ("E2", "(E2) Euro-Meat-Tray 2"),
    ("E4", "(E4) Euro-Meat-Tray 4"),
    ("IP", "(IP) Industrial Pallet"),
    ("IB", "(IB) Intermediate bulk container"),
    ("I1", "(I1) IPP Euro pallet"),
    ("I2", "(I2) I2 IPP half pallet"),
    ("I4", "(I4) I4 IPP quarter pallet"),
    ("P4", "(P4) Paki 1.4"),
    ("PA", "(PA) Parcel/Packet"),
    ("ST", "(ST) Piece"),
    ("KK", "(KK) Plastic jerrican"),
    ("KD", "(KD) Plastic DD pal (customer own)"),
    ("PH", "(PH) Privately-owned Container"),
    ("RC", "(RC) Roll&GOH"),
    ("VG", "(VG) Security cage"),
    ("GB", "(GB) Skeleton box pallet"),
    ("H1", "(H1) Sterile Pallet 1"),
]

# Unified packaging codes list (preserving order without duplicates)
_seen_pkg = set()
DACHSER_PACKAGING_CODES = []
for _code, _label in DACHSER_PACKAGING_T + DACHSER_PACKAGING_F:
    if _code not in _seen_pkg:
        _seen_pkg.add(_code)
        DACHSER_PACKAGING_CODES.append((_code, _label))

DACHSER_PALLET_CODES = {
    "EU",
    "EP",
    "DD",
    "HE",
    "HP",
    "VE",
    "IP",
    "PX",
    "EW",
    "PA",
    "GB",
    "RO",
    "C0",
    "C1",
    "C2",
    "C4",
    "I1",
    "I2",
    "I4",
    "H1",
    "KH",
    "KD",
}

# Label Formats & Barcode Types
DACHSER_LABEL_FORMATS = [
    ("P", "PDF (P)"),
    ("Z", "ZPL - Zebra Printer Language (Z)"),
]

DACHSER_LABEL_TYPES = [
    ("EAN", "EAN (Standard GS1-128 Barcode)"),
    ("DMC", "DMC (2D DataMatrix Code)"),
    ("EAN,DMC", "EAN + DMC (Merged)"),
]

# Collection Options
DACHSER_COLLECTION_OPTIONS = [
    ("CN", "CN - Collection Notification"),
    ("CB", "CB - Collection Booking"),
]

# Delivery Notice Options
DACHSER_DELIVERY_NOTICE_TYPES = [
    ("none", "No Delivery Notice"),
    ("AS", "AS - Shipper Notice by Phone / SMS / Email"),
    ("AI", "AI - Electronic Delivery Notice"),
    ("TE", "TE - Telephone Delivery Notice"),
    ("SM", "SM - SMS Delivery Notice"),
    ("EM", "EM - Email Delivery Notice"),
    ("AV", "AV - Scheduled Delivery Appointment"),
]

# Rate Calculation Modes & Logistics Types
DACHSER_RATE_MODES = [
    (
        "api_with_fallback",
        "API Quotation with Local Tariff Table Fallback (Recommended)",
    ),
    ("api_quotation", "Online API Quotation Only (/rest/v2/quotations)"),
    ("tariff_table", "Local Tariff Table Only (By Zones / Weights / Pallets)"),
]

DACHSER_LOGISTICS_TYPES = [
    ("D", "D - Distribution (Outbound)"),
    ("P", "P - Procurement (Inbound / Return)"),
]

DACHSER_RATE_TYPES = [
    ("fixed", "Fixed Bracket Price"),
    ("per_kg", "Base + Price per Total Kg"),
    ("per_excess_kg", "Base + Price per Excess Kg (above Included Kg)"),
    ("per_100kg", "Base + Price per 100 Kg Fraction"),
    ("per_pallet", "Base + Price per Pallet / Package"),
]

# Reference Codes in Dachser API
DACHSER_REFERENCE_CODES = [
    ("100", "100 - Consignor Order / Delivery Number (Mandatory)"),
    ("101", "101 - Customer Order Reference"),
    ("102", "102 - Origin Document"),
    ("007", "007 - Delivery Note Reference"),
    ("001", "001 - Consignee Purchase Order"),
    ("312", "312 - EKAER Number (Hungary)"),
]

# Text Qualifier Codes in Dachser API
DACHSER_TEXT_CODES = [
    ("ZU", "ZU - Delivery Instructions / Driver Note"),
    ("AB", "AB - Collection Instructions"),
    ("RE", "RE - Invoice Text"),
    ("SO", "SO - Additional Delivery Note Information"),
]

# OCA delivery_state mapping from Dachser status codes
DACHSER_SHIPMENT_STATUS = {
    # unloading / recorded
    "I": "shipping_recorded_in_carrier",
    "E": "shipping_recorded_in_carrier",
    "DFÜ": "shipping_recorded_in_carrier",
    "ORD": "shipping_recorded_in_carrier",
    "1000": "shipping_recorded_in_carrier",
    # loading / transit
    "A": "shipping_recorded_in_carrier",
    "U": "in_transit",
    "B": "in_transit",
    "L": "in_transit",
    "SE": "in_transit",
    "SA": "in_transit",
    "1100": "in_transit",
    "2000": "in_transit",
    # on delivery
    "R": "in_transit",
    "ZUST": "in_transit",
    "3000": "in_transit",
    # delivery differences / incidents
    "K": "incident",
    "H": "incident",
    "N": "incident",
    "S": "incident",
    "9000": "incident",
    # delivered
    "Z": "customer_delivered",
    "AG": "customer_delivered",
    "POD": "customer_delivered",
    "3500": "customer_delivered",
    "4000": "customer_delivered",
    # cancelled
    "X": "canceled_shipment",
}

# Detailed status mapping from Dachser Event Codes to normalized shipment states
DACHSER_EVENT_STATE_MAP = {
    "I": "registered",
    "E": "registered",
    "DFÜ": "registered",
    "ORD": "registered",
    "1000": "registered",
    "A": "in_transit",
    "U": "in_transit",
    "B": "in_transit",
    "L": "in_transit",
    "SE": "in_transit",
    "SA": "in_transit",
    "1100": "in_transit",
    "2000": "in_transit",
    "R": "out_for_delivery",
    "ZUST": "out_for_delivery",
    "3000": "out_for_delivery",
    "Z": "delivered",
    "AG": "delivered",
    "POD": "delivered",
    "3500": "delivered",
    "4000": "delivered",
    "H": "incidence",
    "K": "incidence",
    "N": "incidence",
    "S": "incidence",
    "9000": "incidence",
    "X": "cancelled",
}

DACHSER_SHIPMENT_STATES = [
    ("draft", "Pending Shipment"),
    ("imported", "Draft in eLogistics (Imported)"),
    ("labelled", "Labelled in eLogistics (Labelled)"),
    ("sent", "Transmitted to Dachser TMS (Sent)"),
    ("registered", "Registered at Dachser Branch"),
    ("in_transit", "In Transit"),
    ("out_for_delivery", "Out for Delivery"),
    ("delivered", "Delivered"),
    ("incidence", "Delivery Exception"),
    ("cancelled", "Cancelled"),
]

STATE_TO_DELIVERY_STATE = {
    "draft": "shipping_recorded_in_carrier",
    "imported": "shipping_recorded_in_carrier",
    "labelled": "shipping_recorded_in_carrier",
    "sent": "shipping_recorded_in_carrier",
    "registered": "shipping_recorded_in_carrier",
    "in_transit": "in_transit",
    "out_for_delivery": "in_transit",
    "delivered": "customer_delivered",
    "incidence": "incident",
    "cancelled": "canceled_shipment",
}


def map_dachser_status_to_state(event_code, description=""):
    """Map a Dachser status code or description to one of `DACHSER_SHIPMENT_STATES`."""
    code_up = (str(event_code or "")).strip().upper()
    if code_up in DACHSER_EVENT_STATE_MAP:
        return DACHSER_EVENT_STATE_MAP[code_up]
    desc_low = (description or "").lower()
    if any(k in desc_low for k in ("deliver", "zugestellt", "pod")):
        return "delivered"
    if any(k in desc_low for k in ("out for delivery", "zustellung")):
        return "out_for_delivery"
    if any(
        k in desc_low for k in ("error", "incident", "exception", "refused", "damage")
    ):
        return "incidence"
    if any(k in desc_low for k in ("cancel", "storn")):
        return "cancelled"
    if any(
        k in desc_low
        for k in ("pick", "transit", "hub", "loaded", "departed", "arrived")
    ):
        return "in_transit"
    return "registered"


def map_dachser_status_to_delivery_state(event_code, description=""):
    """Map a Dachser status code or description to OCA `delivery_state` values."""
    code_up = (str(event_code or "")).strip().upper()
    if code_up in DACHSER_SHIPMENT_STATUS:
        return DACHSER_SHIPMENT_STATUS[code_up]
    state = map_dachser_status_to_state(event_code, description)
    return STATE_TO_DELIVERY_STATE.get(state, "shipping_recorded_in_carrier")
