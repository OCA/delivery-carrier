# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RoutificConfig(models.Model):
    _name = "routific.config"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Settings for Routific connexion."
    _order = "sequence,id"

    name = fields.Char(required=True)
    sequence = fields.Integer()
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        string="Company",
    )
    post_endpoint = fields.Char(
        "Post URL", default="https://product-api.routific.com", required=True
    )
    get_endpoint = fields.Char(
        "Get URL", default="https://api.routific.com", required=True
    )
    token = fields.Text(required=True)
    max_stop_lateness = fields.Integer(string="Maximum stop lateness")
    max_driver_overtime = fields.Integer(string="Maximum driver overtime")
    shortest_distance = fields.Boolean(string="Optimize by shortest distance")
    traffic = fields.Float(
        string="Traffic estimation", help="Faster = 1.0 - Slower = 2.0", default=1
    )
    strict_start = fields.Boolean(
        string="Strict start",
        help="""It forces the departure time of a driver to be at ​shift_start​.
        The default is false
        """,
    )
    auto_balance = fields.Boolean(string="Stops distributed across all drivers")
    default_load = fields.Integer(string="Default load of stops", default=1)
    default_duration = fields.Integer(string="Default duration of stops", default=10)
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Allowed operation type",
        required=True,
    )
    address_format = fields.Text(
        string="Address format",
        default="%(street)s, %(city)s, %(state)s, %(zip)s, %(country)s",
        required=True,
    )

    def get_settings(self):
        """With this method we build the settings dictionary that has to be sent
        to Routific.
        """
        return {
            "max_stop_lateness": self.max_stop_lateness,
            "max_driver_overtime": self.max_driver_overtime,
            "shortest_distance": self.shortest_distance,
            "traffic": self.traffic,
            "strict_start": self.strict_start,
            "auto_balance": self.auto_balance,
            "default_load": self.default_load,
            "default_duration": self.default_duration,
        }

    def _routific_header(self):
        """This method does the construction of headers for the requests to the API."""
        self.ensure_one()
        if self.token:
            return {
                "Content-Type": "application/json",
                "Authorization": "Bearer %s" % self.token,
            }
        else:
            raise UserError(_("Token needed to make the comunication with Routific."))

    def send_project(self, json_object):
        """This method is for post the project to Routific."""
        url = self.post_endpoint + "/v1.0/project"
        response = requests.post(url, headers=self._routific_header(), json=json_object)
        if response.status_code != 200:
            raise UserError(
                _("Error on project posting %(code)s \n\n %(response)s")
                % {"code": response.status_code, "response": response.text}
            )
        return response.text

    def send_new_stops(self, routific_project_id, json_object):
        """This method is for post the new stops to a Routific project."""
        url = self.post_endpoint + "/v0.1/project/%s/stops/" % routific_project_id
        response = requests.post(url, headers=self._routific_header(), json=json_object)
        if response.status_code != 200:
            raise UserError(
                _("Error at new stop posting %(code)s \n\n %(response)s")
                % {"code": response.status_code, "response": response.text}
            )
        return response.text

    def get_solution(self, project_id):
        """This method is for get the solution from Routific."""
        url = self.get_endpoint + "/product/projects/%s" % (project_id)
        response = requests.get(url, headers=self._routific_header())
        if response.status_code != 200:
            raise UserError(
                _("Error at new stop posting %(code)s \n\n %(response)s")
                % {"code": response.status_code, "response": response.text}
            )
        return response.text

    @api.constrains("traffic")
    def _check_range_traffic_value(self):
        for rec in self:
            if rec.traffic < 1.0 or rec.traffic > 2.0:
                raise UserError(
                    _("The traffic estimation value must be between 1.0 and 2.0")
                )
