# coding: utf-8
# Copyright (C) 2014 - Today: Akretion (http://www.akretion.com)
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author Aymeric Lecomte <aymeric.lecomte@akretion.com>
# @author David BEAL <david.beal@akretion.com>
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class DropoffSite(models.Model):
    _name = 'dropoff.site'
    _inherits = {'res.partner': 'partner_id'}
    _order = "code, name"

    code = fields.Char(string='Code')

    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True,
        ondelete='cascade')

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier', string='Delivery Method',
        required=True, domain="[('with_dropoff_site', '=', True)]")

    calendar_id = fields.Many2one(
        comodel_name='resource.calendar', string='Calendar', copy=False)

    attendance_ids = fields.One2many(
        'resource.calendar.attendance', related='calendar_id.attendance_ids',
        string='Working Time')

    # Inherit part
    @api.model
    def create(self, vals):
        vals.update({
            'customer': False,
            'supplier': False,
        })
        return super(DropoffSite, self).create(vals)

    @api.multi
    def unlink(self):
        self.mapped('calendar_id').unlink()
        return super(DropoffSite, self).unlink()

    # Action Part
    @api.multi
    def action_enable_calendar(self):
        for site in self:
            if not site.calendar_id:
                site.calendar_id = site.calendar_id.create(
                    site._prepare_calendar_id())

    @api.multi
    def action_disable_calendar(self):
        self.mapped('calendar_id').unlink()

    @api.multi
    def geo_localize(self):
        for site in self:
            site.partner_id.geo_localize()

    # Custom Part
    @api.multi
    def _prepare_calendar_id(self):
        self.ensure_one()
        return {'name': self.name}
