# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields, api
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import RetryableJobError, FailedJobError
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


def chunks(items, length):
    for index in xrange(0, len(items), length):
        yield items[index:index + length]


class SupplierProductProduct(models.Model):
    _name = 'supplier.product.product'
    _inherit = 'supplier.binding'
    _inherits = {'product.product':'odoo_id'}
    _description = 'Supplier Product'

    odoo_id = fields.Many2one(comodel_name='product.product',
                              string='Product',
                              required=True,
                              ondelete='restrict')

    sku = fields.Char('SKU', required=True, readonly=True)
    supplier_name = fields.Char(related='odoo_id.name', required=True, readonly=True)
    supplier_qty = fields.Float(string='Computed Quantity',
                                help="Last computed quantity on Supplier.")

    no_product_sync = fields.Boolean(string='No sync import product')
    compute_stock = fields.Boolean(string='Compute stock from supplier')

    url_product = fields.Char('Url from the product is')

    brand = fields.Char('Brand')

    height = fields.Float('Height', default=0)
    length = fields.Float('Length', default=0)
    weight = fields.Float('Weight', default=0)
    width = fields.Float('Width', default=0)

    discount = fields.Float('Discount on prices of the product (in percentage)')

    RECOMPUTE_QTY_STEP = 1000  # products at a time

    @job(default_channel='root.supplier')
    @api.model
    def import_record(self, backend, external_id):
        if external_id:
            backend.current_importer = external_id[0]
        _super = super(SupplierProductProduct, self)
        try:
            result = _super.import_record(backend, external_id)
        except Exception as e:
            if e.message.find('current transaction is aborted') > -1 or e.message.find('could not serialize access due to concurrent update') > -1:
                raise RetryableJobError('A concurrent job is already exporting the same record '
                                        '(%s). The job will be retried later.' % self.model._name)
            raise e
        if not result:
            raise RetryableJobError('The product can''t be imported (%s)' % external_id, seconds=300)
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'

    supplier_bind_ids = fields.One2many(
        comodel_name='supplier.product.product',
        inverse_name='odoo_id',
        string='Supplier Bindings',
    )

    @api.depends('qty_available', 'virtual_available', 'stock_quant_ids', 'stock_move_ids', 'outgoing_qty',
                 'product_uom_qty', 'product_uom', 'route_id')
    def _compute_check_stock(self):
        compute_stock = None
        if self and self.supplier_bind_ids and len(self.supplier_bind_ids) == 1 and \
                (self.supplier_bind_ids.compute_stock or self.supplier_bind_ids.backend_id.compute_stock) and \
                self.product_tmpl_id.seller_ids:
            for supplier in self.product_tmpl_id.seller_ids:
                backend = self.env['supplier.backend'].search([('supplier_id', '=', supplier.name)])
                if backend and backend.compute_stock:
                    # TODO compute backend supplier quantity
                    return 0

        return super(ProductProduct, self)._compute_check_stock()


class ProductProductAdapter(Component):
    _name = 'supplier.product.product.adapter'
    _inherit = 'supplier.adapter'
    _apply_on = 'supplier.product.product'

    def _call(self, method, arguments):
        try:
            return super(ProductProductAdapter, self)._call(method, arguments)
        except Exception:
            raise

    def get_href_products(self, arguments):
        try:
            return self._call(method='get_href_products', arguments=None)
        except AssertionError:
            _logger.error('There aren\'t (%s) parameters for %s', 'importer', 'get_hrefs_product')
            raise

    def get_product_data_by_href(self, arguments):
        try:
            assert arguments
            if len(arguments) > 2:
                arguments = arguments[1:]
            return self._call(method='get_product_data_by_href', arguments=arguments)
        except AssertionError:
            _logger.error('There aren\'t (%s) parameters for %s', arguments, 'get_product_data_by_href')
            raise

    def get_product_csv_data(self, arguments):
        try:
            assert arguments
            return self._call(method='get_csv_data', arguments=[arguments['importer']])
        except AssertionError:
            _logger.error('There aren\'t (%s) parameters for %s', 'importer', 'get_product_csv_data')
            raise

    def get_field_product_data(self, arguments):
        try:
            assert arguments
            return self._call(method='get_field_product_by_href', arguments=arguments)
        except AssertionError:
            _logger.error('There aren\'t parameters for %s', 'get_field_product_data')
            raise
