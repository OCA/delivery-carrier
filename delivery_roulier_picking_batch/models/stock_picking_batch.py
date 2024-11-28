# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    def _get_default_weight_uom(self):
        return self.env[
            "product.template"
        ]._get_weight_uom_name_from_ir_config_parameter()

    carrier_price = fields.Float(string="Shipping Cost")
    delivery_type = fields.Selection(related="carrier_id.delivery_type", readonly=True)
    carrier_id = fields.Many2one(
        "delivery.carrier", string="Carrier", check_company=True
    )
    weight = fields.Float(
        compute="_compute_weight",
        digits="Stock Weight",
        store=True,
        help="Total weight of the products in the picking.",
        compute_sudo=True,
    )
    carrier_tracking_ref = fields.Char(string="Tracking Reference", copy=False)
    carrier_tracking_url = fields.Char(
        string="Tracking URL", compute="_compute_carrier_tracking_url"
    )
    weight_uom_name = fields.Char(
        string="Weight unit of measure label",
        compute="_compute_weight_uom_name",
        readonly=True,
        default=_get_default_weight_uom,
    )
    sent_package_ids = fields.One2many(
        "stock.quant.package",
        "batch_id",
        string="Packages",
    )

    @api.constrains("carrier_id")
    def _check_carrier_id_is_roulier(self):
        for batch in self:
            if batch.carrier_id and not batch.carrier_id._is_roulier():
                raise UserError(_("Only Roulier carrier is supported"))

    def _compute_weight_uom_name(self):
        for package in self:
            package.weight_uom_name = self.env[
                "product.template"
            ]._get_weight_uom_name_from_ir_config_parameter()

    @api.depends("carrier_id", "carrier_tracking_ref")
    def _compute_carrier_tracking_url(self):
        for batch in self:
            batch.carrier_tracking_url = (
                (
                    # Similar flawed logic as in delivery_roulier
                    batch.picking_ids.package_ids[0]._get_tracking_link()
                    if batch.carrier_tracking_ref
                    and len(batch.picking_ids.package_ids) > 0
                    else False
                )
                if batch.carrier_id and batch.carrier_id._is_roulier()
                else False
            )

    @api.depends("move_ids")
    def _compute_weight(self):
        for batch in self:
            batch.weight = sum(
                move.weight for move in batch.move_ids if move.state != "cancel"
            )

    def cancel_shipment(self):
        for batch in self:
            batch.carrier_id.cancel_shipment(self)
            msg = "Shipment %s cancelled" % batch.carrier_tracking_ref
            batch.message_post(body=msg)
            batch.carrier_tracking_ref = False
            batch.sent_package_ids = [(5, 0, 0)]

    def action_done(self):
        if not self.carrier_id or not (
            self.carrier_id.integration_level == "rate_and_ship"
            and self.picking_type_id.code != "incoming"
        ):
            return super().action_done()

        self.ensure_one()
        pickings = self.picking_ids.filtered(
            lambda picking: picking.state not in ("cancel", "done")
        )
        if pickings.carrier_id - self.carrier_id:
            raise UserError(
                _("Pickings %(pickings)s already have a different carrier")
                % {
                    "pickings": ", ".join(
                        pickings.filtered(
                            lambda p: p.carrier_id and p.carrier_id != self.carrier_id
                        ).mapped("name")
                    )
                }
            )
        pickings.write({"carrier_id": self.carrier_id.id})
        # Delivery Roulier works with packages, so we need to generate a package
        # if it doesn't exist, this is simalar to action_put_in_pack but without
        # the checks
        picking_move_lines = self.move_line_ids
        move_line_ids = picking_move_lines.filtered(
            lambda ml: float_compare(
                ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding
            )
            > 0
            and not ml.result_package_id
        )
        if not move_line_ids:
            move_line_ids = picking_move_lines.filtered(
                lambda ml: float_compare(
                    ml.product_uom_qty,
                    0.0,
                    precision_rounding=ml.product_uom_id.rounding,
                )
                > 0
                and float_compare(
                    ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding
                )
                == 0
            )
        if move_line_ids:
            move_line_ids.picking_id[0]._put_in_pack(move_line_ids, False)

        return super().action_done()

    def open_website_url(self):
        """Open tracking page.

        More than 1 tracking number: display a list of packages
        Else open directly the tracking page
        """
        self.ensure_one()
        if not self.carrier_id or not self.carrier_id._is_roulier():
            return super().open_website_url()

        packages = self.sent_package_ids
        if len(packages) == 0:
            raise UserError(_("No packages found for this picking"))
        elif len(packages) == 1:
            return packages.open_website_url()  # shortpath

        # display a list of pickings
        xmlid = "stock.action_package_view"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("id", "in", packages.ids)]
        action["context"] = {"batch_id": self.id}
        return action
