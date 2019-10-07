# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# This project is based on connector-magneto, developed by Camptocamp SA

from odoo.addons.component.core import Component


class SupplierModelBinder(Component):
    """ Bind records and give odoo/supplier ids correspondence

    Binding models are models called ``supplier.{normal_model}``,
    like ``supplier.res.partner`` or ``supplier.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Supplier ID, the ID of the Supplier Backend and the additional
    fields belonging to the Supplier instance.
    """
    _name = 'supplier.binder'
    _inherit = ['base.binder', 'base.supplier.connector']
    _apply_on = [
        'supplier.product.product',
        'supplier.product.supplierinfo',
    ]
