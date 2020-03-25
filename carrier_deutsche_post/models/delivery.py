from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    carrier_account_id = fields.Many2one('carrier.account', 'Carrier Account')
    product_code = fields.Char('Product Code')
    type = fields.Selection(
        selection='_get_carrier_type_selection', string='Type',
        help="Carrier type (combines several delivery methods)", )

    # delivery_type = fields.Selection(
    #    selection_add=[('deutsche_post', 'Deutsche post')])

    @api.model
    def _get_carrier_type_selection(self):
        return [('deutsche_post', 'deutsche_post')]

    @api.onchange('carrier_account_id')
    def onchange_carrier_account_id(self):
        if self.carrier_account_id:
            self.type = self.carrier_account_id.type

# class DeliveryGrid(models.Model):
#     _inherit = 'delivery.grid'
#
#     carrier_account_id = fields.Many2one(
#         'carrier.account', 'Carrier Account')
#     product_code = fields.Char('Product Code/Key')
# TODO : delivery.grid is no longer exist in 11,
