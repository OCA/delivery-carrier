# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    tnt_consignment_data = fields.Serialized()
    tnt_consignment_mumber = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_date = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_free_circulation = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_sort_split = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_destination_depot = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_destination_depot_day = fields.Integer(
        sparse="tnt_consignment_data"
    )
    tnt_consignment_cluster_code = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_origin_depot = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_product = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_option = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_market = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_transport = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_transit_depot = fields.Char(sparse="tnt_consignment_data")
    tnt_consignment_xray = fields.Char(sparse="tnt_consignment_data")
    tnt_piece_data = fields.Serialized()
    tnt_piece_barcode = fields.Char(sparse="tnt_piece_data")
