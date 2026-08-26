# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# Master Data provided by CTT Express

CTTEXPRESS_SERVICES = [
    ("01V", "VALIJA UNITOQUE DIARIA"),
    ("02V", "VALIJA BITOQUE DIARIA"),
    ("03V", "VALIJA UNITOQUE 3 DIAS"),
    ("04V", "VALIJA BITOQUE 3 DÍAS"),
    ("10H", "10 HORAS"),
    ("13A", "13 HORAS ISLAS"),
    ("13H", "13 HORAS"),
    ("13M", "FRANCIA 13M"),
    ("13O", "OPTICA"),
    ("18M", "FRANCIA 18M"),
    ("19A", "CANARIAS E-COMMERCE"),
    ("19E", "19 E-COMMERCE"),
    ("19H", "19 HORAS"),
    ("48E", "48 E-COMMERCE"),
    ("48H", "48 HORAS"),
    ("48M", "48 CANARIAS MARITIMO"),
    ("48N", "48H NUEVOS CLIENTES"),
    ("48P", "48 E-COMMERCE NUEVOS CLIENTES"),
    ("63E", "RECOGERAN E-COMMERCE CANARIAS"),
    ("63P", "PUNTOS CERCANÍA"),
    ("63R", "RECOGERAN EN AGENCIA"),
    ("80I", "GLOBAL EXPRESS"),
    ("80R", "GLOBAL RECOGIDA INTERNACIONAL"),
    ("80T", "GLOBAL EXPRESS"),
    ("81I", "TERRESTRE ECONOMY"),
    ("81R", "RECOGIDA TERRESTRE ECONOMY"),
    ("81T", "TERRESTRE ECONOMY"),
    ("830", "8.30 HORAS"),
    ("93T", "TERRESTE E-COMMERCE"),
]

CTTEXPRESS_DELIVERY_STATES_STATIC = {
    "0": "shipping_recorded_in_carrier",  # PENDIENTE DE ENTRADA EN RED
    "1": "in_transit",  # EN TRANSITO
    "2": "in_transit",  # EN REPARTO
    "3": "customer_delivered",  # ENTREGADO
    "4": "incident",  # INCIDENCIA
    "5": "incident",  # DEVOLUCION
    "6": "in_transit",  # RECOGERAN EN AGENCIA
    "7": "incident",  # RECANALIZADO
    "8": "incident",  # NO REALIZADO
    "9": "incident",  # RETORNADO
    "10": "in_transit",  # EN ADUANA
    "11": "in_transit",  # EN AGENCIA
    "12": "customer_delivered",  # ENTREGA PARCIAL
    "13": "incident",  # POSICIONADO EN PER
    "50": "incident",  # DEVOLUCION DESDE PLATAFORMA
    "51": "incident",  # DEVOLUCION SINIESTROS MERCANCIA YA EVALUADA
    "70": "incident",  # RECANALIZADO A SINIESTROS POR PLATAFORMA
    "71": "incident",  # REENCAMINADO
    "90": "canceled_shipment",  # ANULADO
    "91": "in_transit",  # REACTIVACION ENVIO (TOL)
    "99": "in_transit",  # COMPUESTO
}
