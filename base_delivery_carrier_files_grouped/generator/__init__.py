# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import file_generator
from .file_generator import GroupedCarrierFileGenerator
from .file_generator import new_file_generator
from odoo.addons.base_delivery_carrier_files.models import delivery_carrier_file as base_carrier_file
base_carrier_file.new_file_generator = new_file_generator
