# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RoutificProject(models.Model):
    _name = "routific.project"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Project for Routific"

    def _default_routific_config_id(self):
        config_ids = self.env["routific.config"].search([])
        if config_ids:
            return min(config_ids, key=lambda rc: rc.sequence)

    def _default_project_driver_ids(self):
        active_drivers = self.env["res.partner"].search(
            [("is_routific_driver", "=", True), ("routific_driver_active", "=", True)]
        )
        project_drivers = self.env["routific.project.driver"]
        for driver in active_drivers:
            project_drivers = project_drivers + project_drivers.create(
                {"driver_id": driver.id}
            )
        return project_drivers

    name = fields.Char(readonly=True, default="New", copy=False, required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        string="Company",
        required=True,
    )
    routific_project_id = fields.Char(string="Routific project id")
    date = fields.Date(default=date.today() + timedelta(days=1), required=True)
    project_driver_ids = fields.One2many(
        comodel_name="routific.project.driver",
        inverse_name="project_id",
        string="Drivers",
        required=True,
        default=_default_project_driver_ids,
    )
    picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Stops",
        required=True,
        domain="[('id', '=', allowed_picking_ids)]",
    )
    allowed_picking_ids = fields.Many2many(
        comodel_name="stock.picking", compute="_compute_allowed_picking_ids"
    )
    has_new_picking = fields.Boolean(compute="_compute_has_new_picking")
    state = fields.Selection(
        selection=[("draft", "Draft"), ("send", "Sent")],
        string="Status",
        readonly=True,
        default="draft",
        help="""
            * The 'Draft' is used when a user create a new project\n
            * The 'Sent' is used when the project is sended to Routific
        """,
    )
    routific_config_id = fields.Many2one(
        comodel_name="routific.config",
        string="Settings",
        required=True,
        default=_default_routific_config_id,
    )
    json_send = fields.Text()
    json_retrieve = fields.Text()
    json_solution = fields.Text()

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("routific.project")
        res = super().create(vals)
        # Fill the "picking_ids.routific_project_id" with the ID of the created project.
        for picking in res.picking_ids:
            picking.routific_project_id = res.id
            picking.routific_stop_id = False
        return res

    def write(self, vals):
        res = super().write(vals)
        # Fill the "picking_ids.routific_project_id" with the ID of the created project.
        if vals.get("picking_ids"):
            for picking in self.picking_ids:
                if picking.routific_project_id.id != self.id:
                    picking.routific_stop_id = False
                picking.routific_project_id = self.id
        return res

    def _get_drivers(self):
        """With this method we get the info of all drivers selected."""
        drivers = []
        for driver in self.project_driver_ids.mapped("driver_id"):
            vals = driver.get_routific_data(self.routific_config_id)
            drivers.append(vals)
        return drivers

    def _get_stops(self, picking_ids):
        """With this method we get the info of all stops selected."""
        stops = []
        for stop in picking_ids:
            if stop.picking_type_id == self.routific_config_id.picking_type_id:
                value = stop.get_routific_data(self.routific_config_id)
                stops.append(value)
        return stops

    def _get_all_stops(self):
        return self._get_stops(self.picking_ids)

    def send_project(self):
        """With this method we make the dictionary that has to be posted and we process
        the response.
        """
        data = {
            "name": self.name,
            "date": self.date.strftime("%Y-%m-%d"),
            "drivers": self._get_drivers(),
            "stops": self._get_all_stops(),
            "settings": self.routific_config_id.get_settings(),
        }
        json_str = json.dumps(data) + "\n"
        self.json_send = self.json_send + json_str if self.json_send else json_str
        res = self.routific_config_id.send_project(data)
        json_str = res + "\n"
        self.json_retrieve = (
            self.json_retrieve + json_str if self.json_retrieve else json_str
        )
        res = json.loads(res)
        self.routific_project_id = res.get("id")
        self._set_routific_stop_id(res.get("stops", []))
        self._set_routific_driver_id(res.get("drivers", []))
        self.state = "send"

    def _set_routific_driver_id(self, drivers):
        """Set the id of Routific to each routific.project.driver"""
        for driver in drivers:
            id_start = driver["name"].index("[") + 1
            id_end = driver["name"].index("]")
            partner_id = int(driver["name"][id_start:id_end])
            project_driver = self.project_driver_ids.filtered(
                lambda d: d.driver_id.id == partner_id
            )
            project_driver.routific_driver_id = driver["id"]

    def _set_routific_stop_id(self, stops):
        """Set the id of Routific to each stock.picking"""
        for stop in stops:
            picking = self.picking_ids.search(
                [("id", "=", int(stop.get("custom_notes", {}).get("picking_id")))]
            )
            picking.routific_stop_id = stop.get("id")

    def get_solution(self):
        """Method that process the solution"""
        res = self.routific_config_id.get_solution(self.routific_project_id)
        json_str = res + "\n"
        self.json_solution = (
            self.json_solution + json_str if self.json_solution else json_str
        )
        res = json.loads(res)
        solution = res.get("solution")
        if solution:
            routes = solution.get("routes", [])
            for route in routes:
                project_driver_id = self.project_driver_ids.filtered(
                    lambda pd: pd.routific_driver_id == route["_id"]
                )
                stop_sequence = 0
                for visit in route["visits"]:
                    picking = self.picking_ids.search(
                        [("routific_stop_id", "=", visit["id"])]
                    )
                    if picking:
                        stop_sequence += 1
                        picking.routific_stop_sequence = stop_sequence
                        picking.driver_id = project_driver_id.driver_id
        else:
            raise UserError(
                _(
                    "You have not optimice the route on Routific Platform for get "
                    "the solution."
                )
            )

    def button_send_new_stops(self):
        data = self._get_stops(
            self.picking_ids.filtered(lambda p: not p.routific_stop_id)
        )
        json_str = json.dumps(data) + "\n"
        self.json_send = self.json_send + json_str if self.json_send else json_str
        res = self.routific_config_id.send_new_stops(self.routific_project_id, data)
        json_str = res + "\n"
        self.json_retrieve = (
            self.json_retrieve + json_str if self.json_retrieve else json_str
        )
        res = json.loads(res)
        self._set_routific_stop_id(res)

    @api.depends("routific_config_id")
    def _compute_allowed_picking_ids(self):
        for record in self:
            record.allowed_picking_ids = self.env["stock.picking"].search(
                [
                    (
                        "picking_type_id",
                        "=",
                        record.routific_config_id.picking_type_id.id,
                    ),
                    ("state", "=", "assigned"),
                    ("driver_id", "=", False),
                ]
            )

    @api.depends("picking_ids")
    def _compute_has_new_picking(self):
        for record in self:
            new_pickings = record.picking_ids.filtered(lambda p: not p.routific_stop_id)
            if new_pickings and record.state == "send":
                self.has_new_picking = True
            else:
                self.has_new_picking = False

    @api.onchange("picking_ids")
    def _onchange_picking_ids(self):
        actual_pickings = self.env["stock.picking"]
        for picking in self.picking_ids:
            actual_pickings += picking._origin
        deleted_pickings = self._origin.picking_ids - actual_pickings
        for picking in deleted_pickings:
            if picking.routific_stop_id:
                raise UserError(_("You can't delete a stop sent to routific"))

    def action_affected_picking_tree_view(self):
        return {
            "name": _("Pickings"),
            "view_mode": "tree",
            "res_model": "stock.picking",
            "view_id": False,
            "views": [(self.env.ref("connector_routific.vpicktree").id, "tree")],
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.picking_ids.ids)],
            "context": {"create": False},
        }
