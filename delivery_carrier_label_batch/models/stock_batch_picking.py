# -*- coding: utf-8 -*-
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from openerp import _, api, fields, models


class StockBatchPicking(models.Model):

    """ Add carrier and carrier options on batch

    to be able to massively set those options on related picking.

    """
    _inherit = "stock.batch.picking"

    carrier_id = fields.Many2one(
        'delivery.carrier', 'Carrier',
        states={'done': [('readonly', True)]})
    option_ids = fields.Many2many(
        'delivery.carrier.option',
        string='Options')

    @api.multi
    def action_set_options(self):
        """ Apply options to picking of the batch

        This will replace all carrier options in picking

        """
        for rec in self:
            options_datas = {
                'carrier_id': rec.carrier_id.id,
                'option_ids': [(6, 0, rec.option_ids.ids)],
            }
            rec.picking_ids.write(options_datas)

    @api.multi
    def _get_options_to_add(self, carrier=None):
        carrier = carrier or self.carrier_id
        options = carrier.available_option_ids
        return options.filtered(lambda rec: rec.mandatory or rec.by_default)

    @api.onchange('carrier_id')
    def carrier_id_change(self):
        """ Inherit this method in your module """
        if self.carrier_id:
            # This can look useless as the field carrier_code and
            # carrier_type are related field. But it's needed to fill
            # this field for using this fields in the view. Indeed the
            # module that depend on delivery base can hide some field
            # depending of the type or the code

            available_options = self.carrier_id.available_option_ids
            self.option_ids = self._get_options_to_add()
            self.carrier_type = self.carrier_id.type
            self.carrier_code = self.carrier_id.code
            return {'domain': {
                'option_ids': [('id', 'in', available_options.ids)],
            }}
        return {}

    @api.onchange('option_ids')
    def option_ids_change(self):
        res = {}
        if not self.carrier_id:
            return res
        for available_option in self.carrier_id.available_option_ids:
            if (available_option.mandatory and
                    available_option not in self.option_ids):
                res['warning'] = {
                    'title': _('User Error !'),
                    'message': _("You can not remove a mandatory option."
                                 "\nPlease reset options to default.")
                }
                # Due to https://github.com/odoo/odoo/issues/2693 we cannot
                # reset options
                # self.option_ids = self._get_options_to_add()
        return res

    @api.multi
    def _values_with_carrier_options(self, values):
        values = values.copy()
        carrier_id = values.get('carrier_id')
        option_ids = values.get('option_ids')
        if carrier_id and not option_ids:
            carrier = self.env['delivery.carrier'].browse(carrier_id)
            options = self._get_options_to_add(carrier)
            if options:
                values.update(option_ids=[(6, 0, options.ids)])
        return values

    @api.multi
    def write(self, values):
        """ Set the default options when the delivery method is changed.

        So we are sure that the options are always in line with the
        current delivery method.

        """
        values = self._values_with_carrier_options(values)
        return super(StockBatchPicking, self).write(values)

    @api.model
    def create(self, values):
        """ Set the default options when the delivery method is set on creation

        So we are sure that the options are always in line with the
        current delivery method.

        """
        values = self._values_with_carrier_options(values)
        return super(StockBatchPicking, self).create(values)
