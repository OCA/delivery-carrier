# Copyright 2012-2015 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        states={"done": [("readonly", True)]},
    )
    carrier_code = fields.Char(related="carrier_id.code", readonly=True)
    option_ids = fields.Many2many(
        comodel_name="delivery.carrier.option", string="Options"
    )

    def get_shipping_label_values(self, label):
        self.ensure_one()
        return {
            "name": label["name"],
            "res_id": self.id,
            "res_model": "stock.picking",
            "datas": label["file"],
            "file_type": label["file_type"],
        }

    def attach_shipping_label(self, label):
        """Attach a label returned by generate_shipping_labels to a picking"""
        self.ensure_one()
        data = self.get_shipping_label_values(label)
        if label.get("package_id"):
            data["package_id"] = label["package_id"]
            if label.get("tracking_number"):
                self.env["stock.quant.package"].browse(label["package_id"]).write(
                    {"parcel_tracking": label.get("tracking_number")}
                )
        context_attachment = self.env.context.copy()
        # remove default_type setted for stock_picking
        # as it would try to define default value of attachement
        if "default_type" in context_attachment:
            del context_attachment["default_type"]
        return (
            self.env["shipping.label"].with_context(**context_attachment).create(data)
        )

    def _set_a_default_package(self):
        """Pickings using this module must have a package
        If not this method put it one silently
        """
        for picking in self:
            move_lines = picking.move_line_ids.filtered(
                lambda s: not s.result_package_id
            )
            if move_lines:
                picking._put_in_pack(move_lines)

    def send_to_shipper(self):
        self.ensure_one()
        if self.env.context.get("set_default_package", True):
            self._set_a_default_package()
        # We consider that label has already been generated in case we have a
        # carrier tracking ref, this way we may print the labels before shipping
        # and not generated in second time during shipment
        if self.carrier_tracking_ref:
            return
        else:
            return super().send_to_shipper()

    @api.onchange("carrier_id")
    def onchange_carrier_id(self):
        """Inherit this method in your module"""
        if not self.carrier_id:
            return
        # This can look useless as the field carrier_code and
        # carrier_type are related field. But it's needed to fill
        # this field for using this fields in the view. Indeed the
        # module that depend of delivery base can hide some field
        # depending of the type or the code
        carrier = self.carrier_id
        self.update(
            {"delivery_type": carrier.delivery_type, "carrier_code": carrier.code}
        )
        default_options = carrier.default_options()
        self.option_ids = [(6, 0, default_options.ids)]

    @api.onchange("option_ids")
    def onchange_option_ids(self):
        if not self.carrier_id:
            return
        carrier = self.carrier_id
        for available_option in carrier.available_option_ids:
            if (
                available_option.mandatory
                and available_option.id not in self.option_ids.ids
            ):
                # XXX the client does not allow to modify the field that
                # triggered the onchange:
                # https://github.com/odoo/odoo/issues/2693#issuecomment-56825399
                # Ideally we should add the missing option
                raise UserError(
                    _(
                        "You should not remove a mandatory option."
                        "Please cancel the edit or "
                        "add back the option: %s."
                    )
                    % available_option.name
                )

    @api.model
    def _values_with_carrier_options(self, values):
        values = values.copy()
        carrier_id = values.get("carrier_id")
        option_ids = values.get("option_ids")
        if carrier_id and not option_ids:
            carrier_obj = self.env["delivery.carrier"]
            carrier = carrier_obj.browse(carrier_id)
            default_options = carrier.default_options()
            if default_options:
                values.update(option_ids=[(6, 0, default_options.ids)])
        return values

    def write(self, vals):
        """Set the default options when the delivery method is changed.

        So we are sure that the options are always in line with the
        current delivery method.

        """
        vals = self._values_with_carrier_options(vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Trigger onchange_carrier_id on create

        To ensure options are setted on the basis of carrier_id copied from
        Sale order or defined by default.

        """
        for vals in vals_list:
            vals = self._values_with_carrier_options(vals)
        return super().create(vals_list)

    def _get_label_sender_address(self):
        """On each carrier label module you need to define
        which is the sender of the parcel.
        The most common case is 'picking.company_id.partner_id'
        and then choose the contact which has the type 'delivery'
        which is suitable for each delivery carrier label module.
        But your client might want to customize sender address
        if he has several brands and/or shops in his company.
        In this case he doesn't want his customer to see
        the address of his company in his transport label
        but instead, the address of the partner linked to his shop/brand

        To reach this modularity, call this method to get sender address
        in your delivery_carrier_label_yourcarrier module, then every
        developer can manage specific needs by inherit this method in
        module like :
        delivery_carrier_label_yourcarrier_yourproject.
        """
        self.ensure_one()
        partner = self.company_id.partner_id
        address_id = partner.address_get(adr_pref=["delivery"])["delivery"]
        return self.env["res.partner"].browse(address_id)

    def _check_existing_shipping_label(self):
        """Check that labels don't already exist for this picking"""
        self.ensure_one()
        labels = self.env["shipping.label"].search(
            [("res_id", "=", self.id), ("res_model", "=", "stock.picking")]
        )
        if labels:
            raise UserError(
                _(
                    "Some labels already exist for the picking %s.\n"
                    "Please delete the existing labels in the "
                    "attachments of this picking and try again"
                )
                % self.name
            )
