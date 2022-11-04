# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import datetime
import json
from functools import partial
from unittest.mock import patch

import requests

import odoo
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase

PATH = "odoo.addons.connector_routific.models.routific_config.requests"
patch_post = partial(patch, PATH + ".post")
patch_get = partial(patch, PATH + ".get")


@odoo.tests.tagged("post_install", "-at_install")
class TestConnectorRoutific(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Operation types
        operation_form = Form(cls.env["stock.picking.type"])
        operation_form.name = "Test delivery type"
        operation_form.sequence_code = "TDT"
        operation_form.code = "outgoing"
        cls.operation_type = operation_form.save()
        # Config creation
        config_form = Form(cls.env["routific.config"])
        config_form.name = "Test config"
        config_form.token = "API_TOKEN"
        config_form.picking_type_id = cls.operation_type
        cls.config = config_form.save()
        cls.config.sequence = -1
        # Country Creation
        country = cls.env.ref("base.us")
        # State Creation
        state = cls.env["res.country.state"].create(
            {"name": "Some state", "code": "02", "country_id": country.id}
        )
        # Clients Creation
        cls.client_1 = cls.env["res.partner"].create(
            {
                "name": "Test client 1",
                "street": "Some street 1",
                "city": "Some city",
                "state_id": state.id,
                "zip": "12345",
                "country_id": country.id,
            }
        )
        cls.client_2 = cls.env["res.partner"].create(
            {
                "name": "Test client 2",
                "street": "Some street 2",
                "city": "Some city",
                "state_id": state.id,
                "zip": "12345",
                "country_id": country.id,
            }
        )
        # Driver Creation
        cls.env.company.partner_id.street = "Some street origin"
        cls.env.company.partner_id.city = "Some city"
        cls.env.company.partner_id.state_id = state
        cls.env.company.partner_id.zip = "12345"
        cls.env.company.partner_id.country_id = country
        cls.driver_1 = cls.env["res.partner"].create(
            {
                "name": "Test Driver 1",
                "company_type": "person",
                "is_routific_driver": True,
                "routific_driver_active": True,
                "routific_start": 9.0,
                "routific_end": 12.0,
                "partner_start_id": cls.env.company.partner_id.id,
            }
        )
        # Product Creation
        cls.product = cls.env["product.product"].create(
            {"name": "Storable product", "type": "product"}
        )
        cls.wh1 = cls.env["stock.warehouse"].create(
            {"name": "TEST WH1", "code": "TST1"}
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.wh1.lot_stock_id.id,
                "quantity": 100.0,
            }
        )
        # Pickings Creation
        cls.picking_1 = cls.env["stock.picking"].create(
            {
                "location_id": cls.wh1.lot_stock_id.id,
                "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                "picking_type_id": cls.operation_type.id,
                "partner_id": cls.client_1.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "location_id": cls.wh1.lot_stock_id.id,
                            "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                            "product_id": cls.product.id,
                            "product_uom": cls.product.uom_id.id,
                            "product_uom_qty": 10,
                        },
                    )
                ],
            }
        )
        cls.picking_1.state = "assigned"
        cls.picking_2 = cls.env["stock.picking"].create(
            {
                "location_id": cls.wh1.lot_stock_id.id,
                "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                "picking_type_id": cls.operation_type.id,
                "partner_id": cls.client_2.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "location_id": cls.wh1.lot_stock_id.id,
                            "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                            "product_id": cls.product.id,
                            "product_uom": cls.product.uom_id.id,
                            "product_uom_qty": 10,
                        },
                    )
                ],
            }
        )
        cls.picking_2.state = "assigned"

    def _get_header(self):
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer API_TOKEN",
        }

    def _get_post_creation_data(self, project):
        return {
            "name": project.name,
            "date": project.date.strftime("%Y-%m-%d"),
            "drivers": [
                {
                    "name": "Test Driver 1 [%s]" % (self.driver_1.id),
                    "start_location": {
                        "address": (
                            "Some street origin, Some city, Some state, 12345, "
                            "United States"
                        )
                    },
                    "end_location": {
                        "address": (
                            "Some street origin, Some city, Some state, 12345, "
                            "United States"
                        )
                    },
                    "shift_start": "09:00",
                    "shift_end": "12:00",
                    "speed": 1.0,
                    "types": [],
                },
            ],
            "stops": [
                {
                    "name": "Test client 1",
                    "location": {
                        "address": (
                            "Some street 1, Some city, Some state, 12345, United States"
                        )
                    },
                    "types": [],
                    "custom_notes": {"picking_id": str(self.picking_1.id)},
                },
            ],
            "settings": {
                "max_stop_lateness": 0,
                "max_driver_overtime": 0,
                "shortest_distance": False,
                "traffic": 1.0,
                "strict_start": False,
                "auto_balance": False,
                "default_load": 1,
                "default_duration": 10,
            },
        }

    def _get_post_new_data(self, project):
        return [
            {
                "name": "Test client 2",
                "location": {
                    "address": (
                        "Some street 2, Some city, Some state, 12345, United States"
                    )
                },
                "types": [],
                "custom_notes": {"picking_id": str(self.picking_2.id)},
            }
        ]

    def _get_data_for_get(self, project_id):
        return {
            "solution": {
                "routes": [
                    {
                        "_id": project_id.project_driver_ids[0].routific_driver_id,
                        "visits": [
                            {"id": self.picking_1.routific_stop_id},
                            {"id": self.picking_2.routific_stop_id},
                        ],
                    }
                ]
            }
        }

    def _create_project_wiz(self):
        wizard_form = Form(
            self.env["routific.project.creator"].with_context(
                active_ids=self.picking_1.ids
            )
        )
        wizard = wizard_form.save()
        data = wizard.create_project()
        return self.env["routific.project"].browse(data["res_id"])

    def test_wizard_fill_info(self):
        wizard_form = Form(self.env["routific.project.creator"])
        self.assertTrue(self.driver_1 in wizard_form.driver_ids)
        self.assertEqual(wizard_form.config_id, self.config)
        self.assertEqual(
            wizard_form.date,
            datetime.date.today() + datetime.timedelta(days=1),
        )

    def test_project_creation_from_wizard(self):
        project_id = self._create_project_wiz()
        self.assertTrue(
            self.driver_1 in project_id.project_driver_ids.mapped("driver_id")
        )
        self.assertTrue(self.picking_1 == project_id.picking_ids)
        self.assertEqual(project_id.routific_config_id, self.config)
        self.assertEqual(
            project_id.date, datetime.date.today() + datetime.timedelta(days=1)
        )

    def test_bad_connection(self):
        def bad_response():
            response = requests.Response()
            response.status_code = 404
            return response

        project_id = self._create_project_wiz()
        with patch_post(return_value=bad_response()) as post_mock:
            # If the API server returns 404 error, it explodes in user's face
            with self.assertRaises(UserError):
                project_id.send_project()
            # Assert module did the correct API call
            post_mock.assert_called_once_with(
                "https://product-api.routific.com/v1.0/project",
                headers=self._get_header(),
                json=self._get_post_creation_data(project_id),
            )

    def test_full_operation(self):
        project_id = self._create_project_wiz()

        def creation_response():
            response = requests.Response()
            response.status_code = 200
            response.encoding = "utf-8"
            data = self._get_post_creation_data(project_id)
            data["id"] = "project_id"
            data["stops"][0]["id"] = "stop_id_1"
            data["drivers"][0]["id"] = "driver_id_1"
            response._content = json.dumps(data).encode(encoding=response.encoding)
            return response

        def addition_response():
            response = requests.Response()
            response.status_code = 200
            response.encoding = "utf-8"
            data = self._get_post_new_data(project_id)
            data[0]["id"] = "stop_id_2"
            response._content = json.dumps(data).encode(encoding=response.encoding)
            return response

        def get_response():
            response = requests.Response()
            response.status_code = 200
            response.encoding = "utf-8"
            data = self._get_data_for_get(project_id)
            response._content = json.dumps(data).encode(encoding=response.encoding)
            return response

        with patch_post(return_value=creation_response()) as post_mock:
            project_id.send_project()
            # Assert module did the correct API call
            post_mock.assert_called_once_with(
                "https://product-api.routific.com/v1.0/project",
                headers=self._get_header(),
                json=self._get_post_creation_data(project_id),
            )
        # Assert that project, stops and drivers have his ids from Routific
        self.assertEqual(project_id.routific_project_id, "project_id")
        self.assertEqual(self.picking_1.routific_stop_id, "stop_id_1")
        self.assertEqual(
            project_id.project_driver_ids[0].routific_driver_id, "driver_id_1"
        )
        project_id.picking_ids += self.picking_2
        with patch_post(return_value=addition_response()) as post_mock:
            project_id.button_send_new_stops()
            # Assert module did the correct API call
            post_mock.assert_called_once_with(
                "https://product-api.routific.com/v0.1/project/%s/stops/"
                % (project_id.routific_project_id),
                headers=self._get_header(),
                json=self._get_post_new_data(project_id),
            )
        self.assertEqual(self.picking_2.routific_stop_id, "stop_id_2")
        with patch_get(return_value=get_response()) as get_mock:
            project_id.get_solution()
            # Assert module did the correct API call
            get_mock.assert_called_once_with(
                "https://api.routific.com/product/projects/%s"
                % (project_id.routific_project_id),
                headers=self._get_header(),
            )
        self.assertEqual(self.picking_1.driver_id, self.driver_1)
        self.assertEqual(self.picking_2.driver_id, self.driver_1)
