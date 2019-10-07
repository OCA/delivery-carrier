# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# This project is based on connector-magneto, developed by Camptocamp SA

from odoo.addons.component.core import AbstractComponent


class BaseSupplierConnectorComponent(AbstractComponent):
    """ Base Supplier Connector Component

    All components of this connector should inherit from it.
    """

    _name = 'base.supplier.connector'
    _inherit = 'base.connector'
    _collection = 'supplier.backend'
