# -*- coding: utf-8 -*-
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields, exceptions

from ...components.backend_adapter import WebCrawlerAPI

_logger = logging.getLogger(__name__)


class ImporterProductsSupplierWebCrawler(models.Model):
    _name = 'importer.supplier.webcrawler'
    _description = "Web Crawler for Product's Supplier"

    importer_id = fields.One2many('importer.supplier',
                                  'importer_web_id',
                                  string='Importer')

    params_login_ids = fields.One2many('importer.supplier.webscrawler.login.param', 'webcrawler_id',
                                       'Params to login on page (like user and password)')

    agent_browser = fields.Char('Agent browser', default='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0')

    currency_id = fields.Many2one('res.currency')
    tax_included = fields.Boolean('Taxes included', default=False)
    override_images = fields.Boolean('Override images when update products', default=False)

    name = fields.Char('Name', index=True, required=True, translate=True)
    parent_crawler_id = fields.Many2one('importer.supplier.webcrawler', 'Parent Web crawler', index=True,
                                        ondelete='cascade')
    child_crawler_ids = fields.One2many('importer.supplier.webcrawler', 'parent_crawler_id', 'Child Web Crawlers')

    child_expr_ids = fields.One2many('importer.supplier.webscrawler.child.expr', 'webcrawler_child_id',
                                     'Child search expressions')

    url = fields.Char('Url to get data')
    url_login = fields.Char('Url to login')
    url_image = fields.Char('Url base to get images')
    get_products = fields.Boolean(default=False)
    has_pagination = fields.Boolean(default=False)
    next_page_expr_href_ids = fields.One2many('importer.supplier.get.expression',
                                              'webcrawler_id',
                                              'Next page expression')
    discount_percentage = fields.Float('Discount percentage')

    product_box_data_expr_ids = fields.One2many('importer.supplier.get.expression',
                                                'webcrawler_box_prod_data_id',
                                                'Box of the product\'s data expression')

    sku_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_sku_id', 'Sku expression')
    get_url_as_sku = fields.Boolean('Get url as sku', default=False)
    name_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_name_id', 'Name expression')
    ean_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_ean_id', 'Ean expression')
    price_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_price_id', 'Price expression')
    stock_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_stock_id', 'Stock expression')
    type_stock = fields.Selection([('exist', 'If exist'), ('units', 'Units avaiable')],
                                  string='Type import data',
                                  store=True)

    url_image_expr_ids = fields.One2many('importer.supplier.get.expression',
                                         'webcrawler_image_id',
                                         'Url image expression')
    short_description_expr_ids = fields.One2many('importer.supplier.get.expression',
                                                 'webcrawler_short_des_id',
                                                 'Short description expression')
    large_description_expr_ids = fields.One2many('importer.supplier.get.expression',
                                                 'webcrawler_large_des_id',
                                                 'Large description expression')

    brand_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_brand_id', 'Brand expression')
    height_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_height_id', 'Height expression')
    length_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_length_id', 'Length expression')
    weight_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_weight_id', 'Weight expression')
    width_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_width_id', 'Width expression')
    min_qty_expr_ids = fields.One2many('importer.supplier.get.expression', 'webcrawler_min_qty_id', 'Width expression')

    def get_father_of_fathers(self):
        if self.parent_crawler_id:
            return self.parent_crawler_id.get_father_of_fathers()
        return self

    def get_childs(self):
        if self.child_crawler_ids:
            return self.child_crawler_ids

    def get_url_parent(self):
        if self.parent_crawler_id:
            return self.parent_crawler_id.get_url_parent()
        return self.url

    def get_url_image(self):
        if not self.url_image and self.parent_crawler_id:
            return self.parent_crawler_id.get_url_image()
        return self.url_image

    def get_url_login_parent(self):
        if self.parent_crawler_id:
            return self.parent_crawler_id.get_url_login_parent()

        if self.url_login:
            return self.url_login

        return self.url

    def get_taxes_included(self):
        if self.importer_id and self.importer_id.tax_included:
            return self.importer_id.tax_included
        if not self.tax_included and self.parent_crawler_id:
            return self.parent_crawler_id.get_taxes_included()
        return False

    def check_main_fields_expression(self):
        if not self.url:
            raise exceptions.except_orm('Error', 'There isn\'t url on importer')

    def _check_field(self, field_name):
        self.check_main_fields_expression()

        backend = self.get_father_of_fathers().importer_id.backend_id
        backend.current_importer = self.get_father_of_fathers().importer_id
        field_result = None
        with backend.work_on(self.env['supplier.product.product']._name) as work:
            importer = work.component(usage='supplier.product.product.field')
            field_result = importer.run(arguments=([field_name, self]))

        if field_result:
            raise exceptions.except_orm('Info', 'The %s result is: %s' % (field_name, field_result))
        else:
            raise exceptions.except_orm('Error', 'There isn\'t result for the field: %s' % field_name)

    def update_url_child(self):
        '''
        Method that update the url of self based on search of the child crawlers on the father
        :return:
        '''
        childs = self.get_childs()
        if childs:
            for child in childs:
                child.update_url_child()
        # Get the urls and names and update url of self
        if self.parent_crawler_id and self.parent_crawler_id.child_expr_ids:
            env_wizard = self.env['supplier.import.child.crawlers.wizard']
            url_names = env_wizard.pool._get_url_and_names_childs(env_wizard, self.parent_crawler_id)
            for url_name in url_names:
                if url_name[1] == self.name:
                    self.url = url_name[0]

    def check_sku_expression(self):
        self._check_field('sku')

    def check_name_expression(self):
        self._check_field('name')

    def check_price_expression(self):
        self._check_field('price')

    def check_image_expression(self):
        self._check_field('image')

    def check_stock_expression(self):
        self._check_field('stock')

    def check_ean_expression(self):
        self._check_field('ean')

    def check_brand_expression(self):
        self._check_field('brand')

    def check_weight_expression(self):
        self._check_field('weight')

    def check_description_expression(self):
        self._check_field('description')


class SearchExpression(models.Model):
    _name = 'importer.supplier.get.expression'

    webcrawler_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_box_prod_data_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_name_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_sku_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_ean_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_price_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_stock_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_image_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_short_des_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_large_des_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_brand_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_height_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_length_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_weight_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_width_id = fields.Many2one('importer.supplier.webcrawler')
    webcrawler_min_qty_id = fields.Many2one('importer.supplier.webcrawler')

    child_search_name_id = fields.Many2one('importer.supplier.webscrawler.child.expr')
    child_search_url_id = fields.Many2one('importer.supplier.webscrawler.child.expr')

    type_expression = fields.Selection([('xpath', 'Xpath'), ('regexp', 'Regular Expression')],
                                       string='Type of search',
                                       default='xpath',
                                       store=True,
                                       required=True)

    expression = fields.Char(required=True)

    def check_expression(self):
        webcrawler = self.webcrawler_box_prod_data_id or \
                     self.webcrawler_name_id or \
                     self.webcrawler_sku_id or \
                     self.webcrawler_ean_id or \
                     self.webcrawler_price_id or \
                     self.webcrawler_stock_id or \
                     self.webcrawler_image_id or \
                     self.webcrawler_short_des_id or \
                     self.webcrawler_large_des_id or \
                     self.webcrawler_brand_id or \
                     self.webcrawler_height_id or \
                     self.webcrawler_length_id or \
                     self.webcrawler_weight_id or \
                     self.webcrawler_width_id or \
                     self.webcrawler_min_qty_id or \
                     self.child_search_name_id.webcrawler_child_id or \
                     self.child_search_url_id.webcrawler_child_id

        page_content = WebCrawlerAPI.download(webcrawler.url, use_agent=True)
        result = WebCrawlerAPI.execute_get_expression(self, page_content)

        if result:
            raise exceptions.except_orm('Info', 'The result of %s is: %s' % (self.expression, result))
        else:
            raise exceptions.except_orm('Error', 'There isn\'t result for the expression: %s' % self.expression)


class ChildWebcrawlerSearch(models.Model):
    _name = 'importer.supplier.webscrawler.child.expr'

    webcrawler_child_id = fields.Many2one('importer.supplier.webcrawler')

    name_expr_ids = fields.One2many('importer.supplier.get.expression', 'child_search_name_id', 'Name expression')
    url_expr_ids = fields.One2many('importer.supplier.get.expression', 'child_search_url_id', 'Url expression')
    child_get_products = fields.Boolean('Get products in childrens created')
    child_has_pagination = fields.Boolean('Has pagination in childrens created')


class ParamLogin(models.Model):
    _name = 'importer.supplier.webscrawler.login.param'

    webcrawler_id = fields.Many2one('importer.supplier.webcrawler')
    name = fields.Char(required=True)
    param = fields.Char()
