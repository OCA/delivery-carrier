# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import csv
from io import StringIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from osrm import Point

from routingoo.routing_data_matrix import RoutingDataMatrix
from routingoo.vrp_solver import VrpSolver


class RoutingWizard(models.TransientModel):
    """
        A wizard to manage routing with partner.
    """

    _name = 'routing.wizard'
    _description = 'Routing wizard'

    host_osrm = fields.Char(string='Server OSRM', default='osrm:5000')
    start_and_end_partner_id = fields.Many2one(
        'res.partner', string="Start and end location", required=True
    )
    partner_ids = fields.Many2many('res.partner', string="Contact")
    num_vehicles = fields.Integer(
        string="Number of vehicles to do the routing", default=1
    )
    time_max_solver = fields.Integer(
        string="Maximum time for operating solver (in seconde)",
        default=5,
        required=True,
    )
    resolution_criterion = fields.Selection(
        selection=[("distance", "Distance"), ("time", "Time")],
        string="Resolution criterion",
        default="distance",
        required=True,
    )
    heuristic_type = fields.Selection(
        selection=[
            ("FirstSolutionStrategy", "First solution"),
            ("LocalSearchMetaheuristic", "Local search metaheuristic"),
        ],
        string="heuristic type",
        default="FirstSolutionStrategy",
        required=True,
        help="You can find more info on https://developers.google.com/optimization/routing/routing_options",
    )
    heuristic_metaheuristic = fields.Selection(
        selection=[
            ("GUIDED_LOCAL_SEARCH", "Guided local search"),
            ("SIMULATED_ANNEALING", "Simulated annealing"),
            ("TABU_SEARCH", "Tabu search"),
        ],
        string="heuristic",
        default="GUIDED_LOCAL_SEARCH",
        help="You can find more info on https://developers.google.com/optimization/routing/routing_options#local_search_options",
    )
    heuristic_first_solution = fields.Selection(
        selection=[
            ("PATH_CHEAPEST_ARC", "Path cheapest arc"),
            ("EVALUATOR_STRATEGY", "Evaluator strategy"),
            ("GLOBAL_CHEAPEST_ARC", "Global cheapest arc"),
            ("LOCAL_CHEAPEST_ARC", "Local cheapest arc"),
        ],
        string="heuristic",
        default="PATH_CHEAPEST_ARC",
        help="You can find more info on https://developers.google.com/optimization/routing/routing_options#first_sol_options",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res.update({'partner_ids': self._context.get('active_ids')})
        return res

    def action_apply(self):
        """Methode call bye the wizard button to export vehicle instructions.
        """
        self.ensure_one()
        try:
            distance_matrix, duration_matrix = self.get_dist_time_osrm_matrix()
        except ValueError as val_exept:
            raise UserError(
                _("{} : {}").format(val_exept.args[0], val_exept.args[2])
            )
        except Exception as expt:
            raise UserError(_("Error :\n{}\nHost used: {}").format(expt, self.host_osrm))
        if self.resolution_criterion == 'distance':
            matrix = distance_matrix
        elif self.resolution_criterion == 'time':
            matrix = duration_matrix
        if self.heuristic_type == 'FirstSolutionStrategy':
            heuristic = self.heuristic_first_solution
        elif self.heuristic_type == 'LocalSearchMetaheuristic':
            heuristic = self.heuristic_metaheuristic
        routes = self.get_solver_solution(matrix, heuristic)
        partner_route_by_vehicle = self.partner_route_by_vehicle(routes)

        action = self.export_to_csv(partner_route_by_vehicle)
        if not action:
            raise UserError(
                _("Error : in the routing compute of solution")
            )
        return action

    def partner_route_by_vehicle(self, routes):
        vehicle_number = 1
        partner_route_by_vehicle = []
        for route in routes:
            partners_route = self.route_to_partner_route(route)
            partners = self.env['res.partner'].browse(partners_route)
            for partner in partners:
                path_partner_infos = {
                    'name': partner.name,
                    'street': partner.street,
                    'street2': partner.street2,
                    'city': partner.city,
                    'state_id': partner.state_id.name,
                    'zip': partner.zip,
                    'country_id': partner.country_id.name,
                    'vehicle_number': vehicle_number,
                }
                partner_route_by_vehicle.append(path_partner_infos)
            vehicle_number += 1
        return partner_route_by_vehicle

    def route_to_partner_route(self, route):
        partners_route = []
        list_partner_id = [self.start_and_end_partner_id.id]
        list_partner_id += self.partner_ids.mapped('id')
        for place in route:
            partner_id = (
                self.env['res.partner'].browse(list_partner_id[place]).id
            )
            partners_route.append(partner_id)
        return partners_route

    def export_to_csv(self, partner_route_by_vehicle):
        """Export route retrive to csv file/vehicle.
        """
        file_name = "Routing for .csv"
        csv_file = StringIO()
        if partner_route_by_vehicle:
            writer = csv.DictWriter(
                csv_file, fieldnames=list(partner_route_by_vehicle[0])
            )

            writer.writeheader()
            for row in partner_route_by_vehicle:
                writer.writerow(row)
            # create attachment
            datas = base64.encodebytes(csv_file.getvalue().encode("utf-8"))
            attachment = self.env["ir.attachment"].create(
                {"name": file_name, "datas": datas}
            )
            return {
                "type": 'ir.actions.act_url',
                "name": attachment.name,
                "url": "/web/content/{}/{}".format(
                    attachment.id, attachment.name
                ),
            }
        else:
            return False

    def get_dist_time_osrm_matrix(self):
        """Retive from osrm server distance and duration matrix bettwen points.

        - check if the partner are not already geo localize
            - if not we do
        - convert coordinate to OSRM points
        - compute distance and duration matrix
        """
        routing_data_matrix = RoutingDataMatrix(host=self.host_osrm)
        if 0.0 in set(
            self.partner_ids.mapped('partner_latitude')
            + self.partner_ids.mapped('partner_longitude')
        ):
            self.partner_ids.geo_localize()
        if 0.0 in set(
            self.start_and_end_partner_id.mapped('partner_latitude')
            + self.start_and_end_partner_id.mapped('partner_longitude')
        ):
            self.start_and_end_partner_id.geo_localize()
        geo_points = [
            Point(
                latitude=self.start_and_end_partner_id.partner_latitude,
                longitude=self.start_and_end_partner_id.partner_longitude,
            )
        ]
        for partner in self.partner_ids:
            point = Point(
                latitude=partner.partner_latitude,
                longitude=partner.partner_longitude,
            )
            geo_points.append(point)
        return routing_data_matrix.distance_duration_matrix_simple_route(
            geo_points
        )

    def get_solver_solution(self, matrix, heuristic):
        """Call heuristic solver to return routes.
        """
        vrp_solver = VrpSolver(self.num_vehicles)
        routes = vrp_solver.solver_guided_local_search(
            matrix,
            self.time_max_solver,
            heuristic_type=self.heuristic_type,
            heuristic=heuristic,
        )
        return routes
