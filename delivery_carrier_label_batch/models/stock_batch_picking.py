# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from contextlib import contextmanager

from odoo import _, api, fields, models, registry, tools


class StockBatchPicking(models.Model):

    """Add carrier and carrier options on batch

    to be able to massively set those options on related picking.

    """

    _inherit = "stock.picking.batch"

    carrier_id = fields.Many2one(
        "delivery.carrier", "Carrier", states={"done": [("readonly", True)]}
    )
    option_ids = fields.Many2many("delivery.carrier.option", string="Options")

    def action_set_options(self):
        """Apply options to picking of the batch

        This will replace all carrier options in picking

        """
        for rec in self:
            options_datas = {
                "carrier_id": rec.carrier_id.id,
                "option_ids": [(6, 0, rec.option_ids.ids)],
            }
            rec.picking_ids.write(options_datas)

    def _get_options_to_add(self, carrier=None):
        carrier = carrier or self.carrier_id
        options = carrier.available_option_ids
        return options.filtered(lambda rec: rec.mandatory or rec.by_default)

    @contextmanager
    @api.model
    def _do_in_new_env(self):
        # Be careful with the test_enable flag, as this behavior won't be the same on tests.
        # If in test mode, there won't be any concurrent threading.
        if tools.config["test_enable"]:
            yield self.env
            return

        with api.Environment.manage():
            with registry(self.env.cr.dbname).cursor() as new_cr:
                yield api.Environment(new_cr, self.env.uid, self.env.context)

    @api.onchange("carrier_id")
    def carrier_id_change(self):
        """Inherit this method in your module"""
        if self.carrier_id:
            available_options = self.carrier_id.available_option_ids
            default_options = self._get_options_to_add()
            self.option_ids = [(6, 0, default_options.ids)]
            self.carrier_code = self.carrier_id.code
            return {
                "domain": {
                    "option_ids": [("id", "in", available_options.ids)],
                }
            }
        return {}

    @api.onchange("option_ids")
    def option_ids_change(self):
        res = {}
        if not self.carrier_id:
            return res
        for available_option in self.carrier_id.available_option_ids:
            if available_option.mandatory and available_option not in self.option_ids:
                res["warning"] = {
                    "title": _("User Error !"),
                    "message": _(
                        "You can not remove a mandatory option."
                        "\nPlease reset options to default."
                    ),
                }
                # Due to https://github.com/odoo/odoo/issues/2693 we cannot
                # reset options
                # self.option_ids = self._get_options_to_add()
        return res

    def _values_with_carrier_options(self, values):
        values = values.copy()
        carrier_id = values.get("carrier_id")
        option_ids = values.get("option_ids")
        if carrier_id and not option_ids:
            carrier = self.env["delivery.carrier"].browse(carrier_id)
            options = self._get_options_to_add(carrier)
            if options:
                values.update(option_ids=[(6, 0, options.ids)])
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

    @api.model
    def create(self, values):
        """Set the default options when the delivery method is set on creation

        So we are sure that the options are always in line with the
        current delivery method.

        """
        values = self._values_with_carrier_options(values)
        return super().create(values)

    def purge_tracking_references(self):
        for batch in self:
            move_lines = batch.move_line_ids
            packs = move_lines.result_package_id.filtered(
                lambda p: p.parcel_tracking
            )
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

    #WARNING ! Do not call this function unless you know what you do ;-)
    def purge_tracking_references_in_new_env(self):
        """Purge tracking for each picking and destination package"""
        with self._do_in_new_env() as new_env:

            # labels = new_env['shipping.label']
            new_self = self.with_env(new_env)
            new_self.purge_tracking_references()
            # may not be necessary but we leave it here for now
            self.env.cr.commit()



