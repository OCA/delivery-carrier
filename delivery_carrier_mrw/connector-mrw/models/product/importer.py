# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import logging
import re
import urllib
import urllib2
from datetime import datetime

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import InvalidDataError

_logger = logging.getLogger(__name__)


class ProductProductBatchImporter(Component):
    """
    Import the Supplier Products.
    """
    _name = 'supplier.product.product.batch.importer'
    _inherit = 'supplier.delayed.batch.importer'
    _apply_on = 'supplier.product.product'

    def run(self, filters=None):
        importer = filters['importer']
        if importer.importer_type == 'web':
            urls_importers = self.backend_adapter.get_href_products(filters)
            _logger.info('search for url products from supplier %s returned %s',
                         filters, urls_importers)
            product_binding_model = self.env['supplier.product.product']
            for data_to_get_product in urls_importers:
                delayable = product_binding_model.with_delay(priority=1, eta=datetime.now())
                delayable.import_record(self.backend_record, (self.backend_record.current_importer,) + data_to_get_product)

        elif importer.importer_type == 'CSV':
            products = self.backend_adapter.get_product_csv_data(filters)
            if products:
                product_binding_model = self.env['supplier.product.product']
                for product in products:
                    delayable = product_binding_model.with_delay(priority=1, eta=datetime.now())
                    try:
                        delayable.import_record(self.backend_record, (self.backend_record.current_importer, product))
                    except Exception as e:
                        _logger.error('Error trying import record %s' % str(product))


class ProductImportMapper(Component):
    _name = 'supplier.product.product.import.mapper'
    _inherit = 'supplier.import.mapper'
    _apply_on = ['supplier.product.product']

    direct = [('sku', 'sku'),
              ('sku', 'external_id'),
              ('description', 'description'),
              ('url_product', 'url_product'),
              ('height', 'height'),
              ('length', 'length'),
              ('weight', 'weight'),
              ('width', 'width'),
              ('brand', 'brand'),
              ]

    @mapping
    def names(self, record):
        return {'name':record['name']}

    @mapping
    def default_code(self, record):
        return {'default_code':self.backend_record.product_prefix + record['sku']}

    @mapping
    def price(self, record):
        return {'price_unit':self._get_price_from_record(record)}

    @mapping
    def type(self, record):
        return {'type':'product'}

    @mapping
    def active(self, record):
        return {'active':True}

    @mapping
    def purchase_ok(self, record):
        return {'purchase_ok':True}

    @mapping
    def sale_ok(self, record):
        return {'sale_ok':True}

    @mapping
    def backend_id(self, record):
        return {'backend_id':self.backend_record.id}

    @mapping
    def barcode(self, record):
        if record.get('ean'):
            # We are going to search any product that has the same barcode
            product = self.env['product.product'].search([('barcode', '=', record.get('ean'))]) or \
                      self.env['product.template'].search([('barcode', '=', record.get('ean'))]).mapped('product_variant_id')

            if product:
                return None

            return {'barcode':record['ean']}

    @mapping
    def supplier_qty(self, record):
        # If we haven't price, we put the quantity on 0
        if not self._get_price_from_record(record):
            return {'supplier_qty':0}
        if record.get('supplier_qty'):
            record['supplier_qty'] = re.sub("[^0-9^.]", "", str(record['supplier_qty']))
            return {'supplier_qty':record['supplier_qty']}
        return {'supplier_qty':0}

    @mapping
    def odoo_id(self, record):
        if record.get('sku'):
            # We are going to search any product that has the same barcode or default_code
            product = self.env['product.product'].search(['|',
                                                          ('barcode', '=', record.get('ean')),
                                                          ('default_code', '=', self.backend_record.product_prefix + record['sku'])]) or \
                      self.env['product.template'].search(['|',
                                                           ('barcode', '=', record.get('ean')),
                                                           ('default_code', '=', self.backend_record.product_prefix + record['sku'])]).mapped(
                          'product_variant_id')

            if product and len(product) == 1:
                return {'odoo_id':product.id}
        return None

    def _get_price_from_record(self, record):
        if record.get('price'):
            if ',' in record['price'] and '.' in record['price']:
                record['price'] = record['price'].replace('.', '').replace(',', '.')
            elif ',' in record['price']:
                record['price'] = record['price'].replace(',', '.')
            record['price'] = re.sub("[^0-9^.]", "", record['price'])
            return record['price']


class ProductTaxesDiscuountCalculation(Component):
    """ Import data for a record.

        Usually called from importers, in ``_after_import``.
        For instance from the products importer.
    """
    _name = 'supplier.product.taxes.price.importer'
    _inherit = 'supplier.importer'
    _apply_on = ['supplier.product.product']
    _usage = 'supplier.taxes.discount.calc'

    def run(self, backend, binding, product_data):
        discount = product_data.get('discount') or 0
        taxes_id = binding.taxes_id or \
                   backend.env['account.tax'].browse(backend.env['ir.values'].get_default('product.template',
                                                                                          'taxes_id',
                                                                                          company_id=backend.company_id.id))
        if product_data.get('tax_included'):
            for tax_id in taxes_id:
                price = binding.price
                price = price - ((discount * price) / 100)
                taxes = tax_id._compute_amount_taxes_include(price)
                binding.update({
                    'standard_price':price - taxes,
                })


class ProductImporter(Component):
    _name = 'supplier.product.product.importer'
    _inherit = 'supplier.importer'
    _apply_on = ['supplier.product.product']

    def _write_canon(self, binding, product_data):
        if product_data.get('canon_digital_type') and product_data.get('canon_digital_price') and float(product_data.get('canon_digital_price')) > 0:
            canon_tax = self.env['account.tax'].search([('name', '=', product_data['canon_digital_type']),
                                                        (['type_tax_use', '=', 'purchase'])])
            if not canon_tax:
                canon_tax = self.env['account.tax'].create({'name':product_data['canon_digital_type'],
                                                            'type_tax_use':'purchase',
                                                            'amount_type':'fixed',
                                                            'amount':product_data['canon_digital_price']})

            if canon_tax.id not in binding.product_tmpl_id.supplier_taxes_id.mapped('id'):
                binding.odoo_id.product_tmpl_id.write({'supplier_taxes_id':[(4, canon_tax.id)]})

    def _write_brand(self, binding, product_data):
        if product_data.get('brand'):
            brand = self.env['product.brand'].search([('name', '=', product_data['brand'])])
            if not brand:
                result = self.env['product.brand'].create({'name':product_data['brand']})
                product_data['product_brand_id'] = result.id
            elif len(brand) > 1:
                product_data['product_brand_id'] = brand[0].id
            else:
                product_data['product_brand_id'] = brand.id

            binding.product_tmpl_id.write({'product_brand_id':product_data.get('product_brand_id')})
            binding.write({'brand':product_data['brand']})
        else:
            _logger.error("Creating brand product for sku (%s) data (%s)", binding.sku, product_data)

    def _write_images(self, binding):
        if self.supplier_record.get('urls_image'):
            env_image = self.env['base_multi_image.image']
            pool_image = env_image.pool.get('base_multi_image.image')
            # Get images of product
            imgs = env_image.search([('owner_id', '=', binding.odoo_id.product_tmpl_id.id),
                                     ('owner_model', '=', 'product.template')])

            url_ddbb_imgs = imgs.mapped('url')

            imgs_url = imgs.filtered(lambda img:img.storage == 'url')

            # We transform the url to database image
            for img in imgs_url:
                binary = pool_image._get_image_from_url_cached(env_image, img.url)
                img.write({
                    'owner_model':'product.template',
                    'storage':'db',
                    'file_db_store':binary,
                    'owner_id':binding.odoo_id.product_tmpl_id.id,
                })

            if not isinstance(self.supplier_record.get('urls_image'), list):
                self.supplier_record['urls_image'] = [self.supplier_record['urls_image']]

            urls_to_create = [url_image for url_image in self.supplier_record['urls_image']
                              if self.supplier_record.get('urls_image') and
                              (url_image[url_image.find('//:') + 3:] if url_image.find('//:') > -1 else url_image not in url_ddbb_imgs)]
            for url_image in urls_to_create:
                binary = pool_image._get_image_from_url_cached(env_image, url_image)
                if binary:
                    self.env['base_multi_image.image'].create({
                        'owner_model':'product.template',
                        'storage':'db',
                        'file_db_store':binary,
                        'owner_id':binding.odoo_id.product_tmpl_id.id,
                        'url':url_image
                    })

    def _get_supplier_data(self):
        """ Return the raw Supplier data for ``self.external_id`` """
        if self.supplier_record:
            return self.supplier_record

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid

        Raise `InvalidDataError`
        """
        if not data or not data.get('sku') or not data.get('name'):
            raise InvalidDataError

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        self._write_images(binding)
        self._write_brand(binding, self.supplier_record)
        self._write_canon(binding, self.supplier_record)
        binding.product_tmpl_id.default_code = binding.default_code
        binding.product_tmpl_id.product_variant_id = binding.odoo_id
        self.supplier_record['product_tmpl_id'] = binding.product_tmpl_id.id
        self.supplier_record['product_id'] = binding.odoo_id.id
        self.supplier_record['discount'] = binding.discount or self.backend_record.discount or 0
        taxes_calc = self.component(usage='supplier.taxes.discount.calc')
        taxes_calc.run(self.backend_record, binding, self.supplier_record)
        supplierinfo_product = self.env['supplier.product.supplierinfo']
        supplierinfo_product.import_record(self.backend_record, self.supplier_record)

    def run(self, external_id, force=False):
        """ Run the synchronization

        :param external_id: identifier of the record on Supplier
        """
        if external_id and isinstance(external_id, (list, tuple)):
            # If the importer is csv we have the data, else we need get the data from url
            if external_id[0]._name == 'importer.supplier' and external_id[0].importer_csv_id:
                data_product = external_id[1]
            else:
                data_product = self.backend_adapter.get_product_data_by_href(external_id)
                if not data_product:
                    product = self.env['supplier.product.product'].search([('url_product', '=', external_id[2])])
                    if product:
                        data_product['sku'] = product.sku
                        data_product['name'] = product.name
                        data_product['description'] = product.description
                        data_product['url_product'] = product.url_product
                        data_product['height'] = product.height
                        data_product['length'] = product.length
                        data_product['weight'] = product.weight
                        data_product['width'] = product.width
                        data_product['supplier_qty'] = 0
            if data_product:
                self.external_id = data_product.get('sku')
                self.supplier_record = data_product
                _super = super(ProductImporter, self)
                return _super.run(external_id=self.external_id, force=force)


class ProductFieldSupplier(Component):
    """
        Importer to get the field of the product supplier
        It is used for checks
    """
    _name = 'supplier.product.field.importer'
    _inherit = 'supplier.importer'
    _apply_on = ['supplier.product.product']
    _usage = 'supplier.product.product.field'

    def run(self, arguments):
        return self.backend_adapter.get_field_product_data(arguments)
