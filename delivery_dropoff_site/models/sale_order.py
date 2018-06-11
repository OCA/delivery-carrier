# coding: utf-8
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dropoff_site_required = fields.Boolean(
        string='Drop-off Site Required', store=True,
        related='carrier_id.with_dropoff_site')

    final_shipping_partner_id = fields.Many2one(
        comodel_name='res.partner', string='Final Recipient', states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)],
        }, readonly=True,
        help="It is the partner that will pick up the parcel "
        "in the dropoff site.")

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        carrier = self.carrier_id
        partner = self.partner_shipping_id
        if carrier and partner and (
                carrier.with_dropoff_site != partner.is_dropoff_site or (
                    carrier.with_dropoff_site and
                    partner.dropoff_site_carrier_id != carrier)):
            self.partner_shipping_id = False
        if carrier and carrier.with_dropoff_site:
            return {'domain': {'partner_shipping_id': [
                ('dropoff_site_carrier_id', '=', carrier.id)]}}
        else:
            return {'domain': {'partner_shipping_id': [
                ('is_dropoff_site', '=', False)]}}

    @api.onchange('partner_shipping_id')
    def onchange_partner_shipping_id(self):
        if self.partner_shipping_id and\
                self.partner_shipping_id.dropoff_site_id and\
                not self.final_shipping_partner_id:
            self.final_shipping_partner_id = self.partner_id

    def _prepare_procurement_group(self):
        res = super(SaleOrder, self)._prepare_procurement_group()
        res.update({
            'final_shipping_partner_id': self.final_shipping_partner_id.id,
        })
        return res
