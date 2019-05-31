# -*- coding: utf-8 -*-
#This file is part of asm. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

def asm_url(debug=False):
    """
    ASM URL connection

    :param debug: If set to true, use Envialia test URL
    """
    if debug:
        return 'http://wsclientes.asmred.com/b2b.asmx'
    else:
        return 'http://wsclientes.asmred.com/b2b.asmx'

def services():
    services = {
        'ASM14': {'tipo': 'IDA', 'servicio': '1', 'horario': '2', 'description': 'ASM 14'},
        'ASM24': {'tipo': 'IDA', 'servicio': '1', 'horario': '3', 'description': 'ASM 24'},
        'ASM10': {'tipo': 'IDA', 'servicio': '1', 'horario': '0', 'description': 'ASM 10'},
        'SABADOS': {'tipo': 'IDA', 'servicio': '1', 'horario': '5', 'description': 'SABADOS'},
        'MASIVO': {'tipo': 'IDA', 'servicio': '1', 'horario': '4', 'description': 'MASIVO'},
        'RECNAVE': {'tipo': 'IDA', 'servicio': '1', 'horario': '11', 'description': 'REC. EN NAVE'},
        'ECONOMY': {'tipo': 'IDA', 'servicio': '37', 'horario': '18', 'description': 'ECONOMY'},
        'MARITIMO': {'tipo': 'IDA', 'servicio': '6', 'horario': '10', 'description': 'MARITIMO'},
        'PARCELCOURIER': {'tipo': 'IDA', 'servicio': '1', 'horario': '19', 'description': 'PARCEL SHOP COURIER'},
        'PARCELECONOMY': {'tipo': 'IDA', 'servicio': '37', 'horario': '19', 'description': 'PARCEL SHOP ECONOMY'},
        'EUROECONOMY': {'tipo': 'IDA', 'servicio': '54', 'horario': '', 'description': 'EURO ESTANDAR'},
    }
    return services
