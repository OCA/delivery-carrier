# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class BookingProfile(models.Model):
    _name = 'booking.profile'

    name = fields.Char('Description', related='description')
    nr = fields.Integer('Identifier')
    code = fields.Char()
    description = fields.Char()
    carrier_id = fields.Many2one('res.partner', 'Carrier')
    service_level_time_id = fields.Many2one(
        'service.level.time',
        'Service Level Time',
    )
    service_level_other_id = fields.Many2one(
        'service.level.other',
        'Service Level Other',
    )
    incoterms_id = fields.Many2one('stock.incoterms', 'Incoterms')
    costcenter_id = fields.Many2one('cost.center', 'Costcenter')
    mailtype = fields.Integer()

    def _replace_relational_records(self, vals):
        carrier = vals.get('carrier_id')
        service_level_time = vals.get('service_level_time_id')
        service_level_other = vals.get('service_level_other_id')
        incoterms = vals.get('incoterms_id')
        costcenter = vals.get('costcenter_id')
        if carrier:
            rec = self.env['res.partner'].search([
                ('code', '=', carrier)], limit=1)
            if not rec:
                raise ValidationError(_(
                    'Carrier %s set on booking profile %s not found' % (
                        carrier, vals['name'])))
            vals['carrier_id'] = rec.id
        if service_level_time:
            rec = self.env['service.level.time'].search([
                ('code', '=', service_level_time)], limit=1)
            if not rec:
                raise ValidationError(_(
                    'Service Level Time %s set on booking profile %s not found'
                    % (service_level_time, vals['name'])))
            vals['service_level_time_id'] = rec.id
        if service_level_other:
            rec = self.env['service.level.other'].search([
                ('code', '=', service_level_other)], limit=1)
            if not rec:
                raise ValidationError(_(
                    'Service Level Other %s set on booking profile %s'
                    'not found' % (service_level_other, vals['name'])))
            vals['service_level_other_id'] = rec.id
        if incoterms:
            rec = self.env['stock.incoterms'].search([
                ('code', '=', incoterms)], limit=1)
            if not rec:
                raise ValidationError(_(
                    'Incoterms %s set on booking profile %s not found' % (
                        incoterms, vals['name'])))
            vals['incoterms_id'] = rec.id
        if costcenter:
            rec = self.env['cost.center'].search([
                ('code', '=', costcenter)], limit=1)
            if not rec:
                raise ValidationError(_(
                    'Costcenter %s set on booking profile %s not found' % (
                        costcenter, vals['name'])))
            vals['costcenter_id'] = rec.id
        return vals

    @api.model
    def create(self, vals):
        vals = self._replace_relational_records(vals)
        return super(BookingProfile, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self._replace_relational_records(vals)
        return super(BookingProfile, self).write(vals)
