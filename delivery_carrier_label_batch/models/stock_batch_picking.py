# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class StockBatchPicking(models.Model):
    """Add carrier and carrier options on batch

    to be able to massively set those options on related picking.

    """

    _inherit = "stock.picking.batch"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
    )
    option_ids = fields.Many2many(
        comodel_name="delivery.carrier.option",
    )
    option_ids_domain = fields.Binary(
        string="Options domain",
        help="Dynamic domain used for the carrier options",
        compute="_compute_option_ids_domain",
    )

    @api.depends("carrier_id")
    def _compute_option_ids_domain(self):
        for rec in self:
            options_domain = None
            if available_options := self.carrier_id.available_option_ids:
                options_domain = [("id", "in", available_options.ids)]
            rec.option_ids_domain = options_domain

    def action_set_options(self):
        """Apply options to picking of the batch

        This will replace all carrier options in picking

        """
        for rec in self:
            options_datas = {
                "carrier_id": rec.carrier_id.id,
                "option_ids": [Command.set(rec.option_ids.ids)],
            }
            rec.picking_ids.write(options_datas)

    def _get_options_to_add(self, carrier=None):
        carrier = carrier or self.carrier_id
        options = carrier.available_option_ids
        return options.filtered(lambda rec: rec.mandatory or rec.by_default)

    @api.onchange("carrier_id")
    def onchange_carrier_id(self):
        """Inherit this method in your module"""
        if not self.carrier_id:
            return
        default_options = self._get_options_to_add()
        self.option_ids = [Command.set(default_options.ids)]

    @api.onchange("option_ids")
    def onchange_option_ids(self):
        if not self.carrier_id:
            return

        for available_option in self.carrier_id.available_option_ids:
            if available_option.mandatory and available_option not in self.option_ids:
                # Optionally, reset the options to the default values.
                self.option_ids = self._get_options_to_add()
                raise UserError(
                    self.env._(
                        "You cannot remove a mandatory option. "
                        "\nPlease reset options to default."
                    )
                )

    def _values_with_carrier_options(self, values):
        values = values.copy()
        carrier_id = values.get("carrier_id")
        option_ids = values.get("option_ids")
        if carrier_id and not option_ids:
            carrier = self.env["delivery.carrier"].browse(carrier_id)
            options = self._get_options_to_add(carrier)
            if options:
                values.update(option_ids=[Command.set(options.ids)])
        return values

    def write(self, values):
        # - Set the default options when the delivery method is changed (So we
        #   are sure that the options are always in line with the current
        #   delivery method)
        # - Purge all tracking references if a new carrier is applied
        values = self._values_with_carrier_options(values)
        result = super().write(values)
        # If a carrier is removed, tracking references are kept until next
        # carrier change
        if values.get("carrier_id", False):
            self.purge_tracking_references()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Set the default options when the delivery method is set on creation

        So we are sure that the options are always in line with the
        current delivery method.

        """
        for values in vals_list:
            self._values_with_carrier_options(values)
        return super().create(vals_list)

    def purge_tracking_references(self):
        """Purge tracking for each picking and destination package"""
        for batch in self:
            move_lines = batch.move_line_ids
            packs = move_lines.result_package_id.filtered(lambda p: p.parcel_tracking)
            if packs:
                packs.write({"parcel_tracking": False})
            pickings = self.env["stock.picking"].search(
                [
                    ("move_line_ids", "in", move_lines.ids),
                    ("carrier_tracking_ref", "!=", False),
                ]
            )
            if pickings:
                pickings.write({"carrier_tracking_ref": False})
