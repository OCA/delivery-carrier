# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)
from odoo.tests import SavepointCase


class TestRoutingVrp(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # fmt: off
        cls.big_matrix = [
            [0,548,776,696,582,274,502,194,308,194,536,502,388,354,468,776,662,],
            [548,0,684,308,194,502,730,354,696,742,1084,594,480,674,1016,868,1210,],
            [776,684,0,992,878,502,274,810,468,742,400,1278,1164,1130,788,1552,754,],
            [696,308,992,0,114,650,878,502,844,890,1232,514,628,822,1164,560,1358,],
            [582,194,878,114,0,536,764,388,730,776,1118,400,514,708,1050,674,1244,],
            [274,502,502,650,536,0,228,308,194,240,582,776,662,628,514,1050,708,],
            [502,730,274,878,764,228,0,536,194,468,354,1004,890,856,514,1278,480,],
            [194,354,810,502,388,308,536,0,342,388,730,468,354,320,662,742,856,],
            [308,696,468,844,730,194,194,342,0,274,388,810,696,662,320,1084,514,],
            [194,742,742,890,776,240,468,388,274,0,342,536,422,388,274,810,468,],
            [536,1084,400,1232,1118,582,354,730,388,342,0,878,764,730,388,1152,354,],
            [502,594,1278,514,400,776,1004,468,810,536,878,0,114,308,650,274,844,],
            [388,480,1164,628,514,662,890,354,696,422,764,114,0,194,536,388,730,],
            [354,674,1130,822,708,628,856,320,662,388,730,308,194,0,342,422,536,],
            [468,1016,788,1164,1050,514,514,662,320,274,388,650,536,342,0,764,194,],
            [776,868,1552,560,674,1050,1278,742,1084,810,1152,274,388,422,764,0,798,],
            [662,1210,754,1358,1244,708,480,856,514,468,354,844,730,536,194,798,0,],
        ]
        # fmt: on

        cls.small_matrix = [
            [0, 10, 20, 30, 11],
            [10, 0, 50, 60, 70],
            [20, 50, 0, 80, 90],
            [30, 60, 80, 0, 12],
            [11, 70, 90, 12, 0],
        ]

        cls.partner_1 = cls.env['res.partner'].create(
            {
                'name': "Berilac Sackville",
                'street': "59 Maidstone Road HA0 4NU",
                'city': "WEMBLEY",
                'country_id': cls.env.ref('base.mc').id,
            }
        )

        cls.partner_2 = cls.env['res.partner'].create(
            {
                'name': "Test1 Routing",
                'street': "15 Rue Basse",
                'zip': 98000,
                'city': "Monaco",
                'country_id': cls.env.ref('base.mc').id,
            }
        )

        cls.partner_3 = cls.env['res.partner'].create(
            {
                'name': "Test2 Routing",
                'street': "1 Avenue des Pins",
                'zip': 98000,
                'city': "Monaco",
                'country_id': cls.env.ref('base.mc').id,
            }
        )

        cls.partner_4 = cls.env['res.partner'].create(
            {
                'name': "Test3 Routing",
                'street': "Maison de Stephanie de Monaco Avenue Saint-Martin",
                'zip': 98000,
                'city': "Monaco",
                'country_id': cls.env.ref('base.mc').id,
            }
        )

        cls.partner_5 = cls.env['res.partner'].create(
            {
                'name': 'Test Routing Address double location',
                'street': "Musee Oceanographique Monaco",
                'zip': "98000",
                'city': "Monaco",
                'country_id': cls.env.ref('base.mc').id,
            }
        )

        cls.host_osrm = 'osrm:5000'
        cls.time_max_solver = 2
        cls.heuristic_type_firstsolutions = "FirstSolutionStrategy"
        cls.heuristic_first_solution = "PATH_CHEAPEST_ARC"

        cls.routing_wizard_cheapest_arc = cls.env['routing.wizard'].create(
            {
                'start_and_end_partner_id': cls.partner_3.id,
                'partner_ids': [(4, cls.partner_1.id), (4, cls.partner_2.id)],
                'num_vehicles': 1,
                'time_max_solver': 3,
                'resolution_criterion': 'distance',
                'heuristic_type': cls.heuristic_type_firstsolutions,
                'heuristic_metaheuristic': False,
                'heuristic_first_solution': cls.heuristic_first_solution,
            }
        )

    def test_get_solver_solution_path_cheapest_arc_small_matrix(self):
        """
        matrix = small_matrix
        heuristic = PATH_CHEAPEST_ARC
        """
        route = self.routing_wizard_cheapest_arc.get_solver_solution(
            self.small_matrix,
            self.routing_wizard_cheapest_arc.heuristic_first_solution,
        )

        self.assertTrue(route)
        self.assertEqual(
            len(route), self.routing_wizard_cheapest_arc.num_vehicles
        )
        self.assertEqual(len(route[0]), len(self.small_matrix) + 1)

    def test_all_firstsolutionstrategy_small_matrix(self):
        """
        matrix = small_matrix
        heuristic = all first solution strategy heuristics choice
        """

        heuristics = [sel[0] for sel in self.env["routing.wizard"]._fields['heuristic_first_solution'].selection]

        for heuristic in heuristics:
            routing_wizard = self.env['routing.wizard'].create(
                {
                    'start_and_end_partner_id': self.partner_3.id,
                    'partner_ids': [(4, self.partner_1.id), (4, self.partner_2.id)],
                    'num_vehicles': 1,
                    'time_max_solver': 4,
                    'resolution_criterion': 'distance',
                    'heuristic_type': "FirstSolutionStrategy",
                    'heuristic_metaheuristic': False,
                    'heuristic_first_solution': heuristic,
                }
            )
            route = routing_wizard.get_solver_solution(
                self.small_matrix,
                heuristic
            )
            self.assertTrue(route)
            self.assertEqual(
                len(route), self.routing_wizard_cheapest_arc.num_vehicles
            )
            self.assertEqual(len(route[0]), len(self.small_matrix) + 1)

    def test_all_metaheuristic_small_matrix(self):
        """
        matrix = small_matrix
        heuristic = all metaheuristic choice
        """

        heuristics = [sel[0] for sel in self.env["routing.wizard"]._fields['heuristic_metaheuristic'].selection]

        for heuristic in heuristics:
            routing_wizard = self.env['routing.wizard'].create(
                {
                    'start_and_end_partner_id': self.partner_3.id,
                    'partner_ids': [(4, self.partner_1.id), (4, self.partner_2.id)],
                    'num_vehicles': 1,
                    'time_max_solver': 4,
                    'resolution_criterion': 'distance',
                    'heuristic_type': "LocalSearchMetaheuristic",
                    'heuristic_metaheuristic': heuristic,
                    'heuristic_first_solution': False,
                }
            )
            route = routing_wizard.get_solver_solution(
                self.small_matrix,
                heuristic
            )
            self.assertTrue(route)
            self.assertEqual(
                len(route), self.routing_wizard_cheapest_arc.num_vehicles
            )
            self.assertEqual(len(route[0]), len(self.small_matrix) + 1)

    def test_get_solver_solution_path_cheapest_arc_big_matrix(self):
        """
        matrix = big_matrix
        """
        route = self.routing_wizard_cheapest_arc.get_solver_solution(
            self.big_matrix,
            self.routing_wizard_cheapest_arc.heuristic_first_solution,
        )

        self.assertTrue(route)
        self.assertEqual(
            len(route), self.routing_wizard_cheapest_arc.num_vehicles
        )
        self.assertEqual(len(route[0]), len(self.big_matrix) + 1)

    def test_get_solver_solution_path_cheapest_arc_small_matrix_2_vehicles(
        self
    ):
        """
        matrix = small_matrix
        num_vehicles = 2
        """
        self.routing_wizard_cheapest_arc.num_vehicles = 2
        route_2 = self.routing_wizard_cheapest_arc.get_solver_solution(
            self.small_matrix,
            self.routing_wizard_cheapest_arc.heuristic_first_solution,
        )
        self.assertTrue(route_2)
        self.assertEqual(
            len(route_2), self.routing_wizard_cheapest_arc.num_vehicles
        )

    def test_get_dist_time_osrm_matrix(self):
        """
        test osrm part
        """
        distance_matrix, duration_matrix = (
            self.routing_wizard_cheapest_arc.get_dist_time_osrm_matrix()
        )
        self.assertTrue(distance_matrix)
        self.assertTrue(duration_matrix)
        # partner_ids + start_and_end_partner_id
        matrix_size = len(duration_matrix)
        self.assertEqual(
            matrix_size, len(self.routing_wizard_cheapest_arc.partner_ids) + 1
        )
        self.assertEqual(
            matrix_size, len(self.routing_wizard_cheapest_arc.partner_ids) + 1
        )
        # Diagonal of the matrix should be filled by 0
        self.assertEqual(duration_matrix[0][0], 0)
        self.assertEqual(duration_matrix[matrix_size - 1][matrix_size - 1], 0)

    def test_export_to_csv(self):
        """
        test csv export
        """
        routes = [[self.partner_1.id, self.partner_3.id, self.partner_2.id]]
        partner_route_by_vehicle = self.partner_route_by_vehicle(routes)
        action = self.routing_wizard_cheapest_arc.export_to_csv(
            partner_route_by_vehicle
        )
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('name'), 'Routing for vehicle 1.csv')
        self.assertTrue(action['url'])

    def test_partner_route_by_vehicle(self):
        """
        test partner route by vehicle
        """
        routes = [
            [self.partner_1.id, self.partner_3.id, self.partner_2.id],
            [self.partner_4.id, self.partner_5.id, self.partner_2.id],
        ]
        partner_route_by_vehicle = self.partner_route_by_vehicle(routes)
        import pdb; pdb.set_trace()

        self.assertEqual(len(partner_route_by_vehicle), len(routes))

    def test_action_apply(self):
        """
        test global action
        """
        action = self.routing_wizard_cheapest_arc.action_apply()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('name'), 'Routing for vehicle 1.csv')
        self.assertTrue(action['url'])
