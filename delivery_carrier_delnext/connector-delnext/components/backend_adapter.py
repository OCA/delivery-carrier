# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# This project is based on connector-magneto, developed by Camptocamp SA

import csv
import logging
import dateutil.parser
import re
import time
from __builtin__ import staticmethod
import requests
from lxml import html
from lxml.html import HtmlElement
from requests import Response, ConnectionError

from odoo.addons.component.core import AbstractComponent

from odoo import exceptions

_logger = logging.getLogger(__name__)

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class SupplierAPI(object):

    def __init__(self, backend):
        self._backend = backend
        self._api = None
        self._importer = backend.current_importer

    @property
    def api(self):
        if self._api is None:
            if self._importer.importer_type == 'web':
                api = WebCrawlerAPI(self._importer)
            elif self._importer.importer_type == 'CSV':
                api = CsvAPI(self._importer)
            api.__enter__()
            self._api = api
        return self._api

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        return self

    def call(self, method, arguments):
        try:
            return self.api.call(method, arguments)
        except:
            _logger.error("api.call('%s', %s) failed", method, arguments)
            raise


class CsvAPI(object):

    def __init__(self, importer):
        self._importer = importer

    def __enter__(self, *args, **kwargs):
        return self

    def call(self, method, arguments):
        try:
            return getattr(self, '_' + method)(*arguments)
        except:
            _logger.error("CsvAPI.call('%s', %s) failed", method, arguments)
            raise

    def _get_csv_data(self, importer):
        list_product = []
        url = None
        if '%s' in importer.importer_csv_id.url:
            url = importer.importer_csv_id.url % (importer.importer_csv_id.user, importer.importer_csv_id.password)
        else:
            url = importer.importer_csv_id.url
        if url:
            # TODO write the content of the url on a file and read the file. After, delete the file
            res_request = requests.get(url)
            if res_request.status_code == requests.codes.ok:
                file_temp = open('/tmp/temp_file_' + str(importer.id) + '.csv', 'w')
                file_temp.write(res_request.content)
                file_temp.close()
                reader = csv.reader(res_request.iter_lines(),
                                    delimiter=str(importer.importer_csv_id.delimiter),
                                    lineterminator=str(importer.importer_csv_id.lineterminator), )
                first_row = True
                try:
                    for row in reader:
                        if first_row and importer.importer_csv_id.has_title_row:
                            first_row = False
                            continue
                        first_row = False
                        prod = {}
                        for relation in importer.importer_csv_id.relation_column_ids:
                            if len(row) > relation.num_column and row[relation.num_column]:
                                try:
                                    prod[relation.field_product] = row[relation.num_column].encode('utf-8')
                                except UnicodeDecodeError as e:
                                    prod[relation.field_product] = row[relation.num_column].decode('unicode_escape').encode('utf-8')

                        prod['tax_included'] = importer.tax_included
                        list_product.append(prod)
                except Exception as e:
                    _logger.error("An error has been produced getting csv")

                '''
                try:
                    os.remove('/tmp/temp_file_' + str(importer.id) + '.csv')
                except OSError as e:
                    _logger.error("The file %s doesn't exist" % '/tmp/temp_file_' + str(importer.id) + '.csv')
                '''

        return list_product


class WebCrawlerAPI(object):

    def __init__(self, importer):
        self._importer = importer
        self._urls_to_get_href_product = []
        self._session = None

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        return self

    def call(self, method, arguments):
        try:
            if arguments:
                return getattr(self, '_' + method)(*arguments)
            return getattr(self, '_' + method)(None)
        except:
            _logger.error("WebCrawlerAPI.call('%s', %s) failed", method, arguments)
            raise

    def _get_isoformat_date(self, date):
        try:
            date = dateutil.parser.parse(date).isoformat()
        except:
            date = ''
        return date

    @staticmethod
    def download(url, use_agent=False, repeat=True):
        if use_agent:
            session = requests.session()
            session.headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0'}
            try:
                r = session.get(url)
                if r.status_code == 200:
                    return r.text
                _logger.error("! Error {} retrieving url {}\n".format(r.status_code, url))
                return None
            except ConnectionError as e:
                if repeat:
                    time.sleep(5)
                    return WebCrawlerAPI.download(url, use_agent=use_agent, repeat=False)
        try:
            r = requests.get(url)
            if r.status_code != 200:
                _logger.error("! Error {} retrieving url {}\n".format(r.status_code, url))
                return None
        except ConnectionError as e:
            if repeat:
                time.sleep(5)
                return WebCrawlerAPI.download(url, use_agent=use_agent, repeat=False)

        return r

    @staticmethod
    def execute_get_expression(expression, page_detail):
        if expression.type_expression == 'xpath':
            if isinstance(page_detail, unicode) and not isinstance(page_detail, Response):
                tree_detail = html.fromstring(page_detail, parser=html.HTMLParser(encoding='utf-8'))
            else:
                tree_detail = html.fromstring(page_detail.content, parser=html.HTMLParser(encoding='utf-8'))
            try:
                res_data = tree_detail.xpath(expression.expression)
            except Exception, e:
                raise exceptions.except_orm('Error', 'Se está intentando ejecutar la siguiente expresión xpath: ' +
                                            str(expression.expression) +
                                            '\\n y está generando el siguiente error: ' + str(e.message))
            if res_data:
                list_data = []
                if res_data and (isinstance(res_data, str) or isinstance(res_data, unicode)):
                    list_data.append(res_data.lstrip())
                else:
                    for data in res_data:
                        if (isinstance(data, str) or isinstance(data, unicode)) and data.lstrip():
                            list_data.append(data.lstrip())
                        elif isinstance(data, HtmlElement) and data.text and data.text.lstrip():
                            list_data.append(data.text.lstrip())
                return list_data

        elif expression.type_expression == 'regexp':
            if isinstance(page_detail, unicode) and not isinstance(page_detail, Response):
                res_data = re.search(expression.expression, page_detail)
            else:
                res_data = re.search(expression.expression, page_detail.content)

            if res_data and len(res_data.groups()):
                return [res_data.group(len(res_data.groups()))]

        return []

    def _get_field_from_parents(self, importer, name_field):
        if importer._fields.get(name_field) and not importer[name_field] and importer.parent_crawler_id:
            return self._get_field_from_parents(importer.parent_crawler_id, name_field)
        elif importer._fields.get(name_field) and importer[name_field]:
            return importer[name_field]
        return None

    def _get_url_content(self, url, session, importer=None, repeat=True):
        if not session:
            session = self._get_session(importer)
        # fetch the login page
        try:
            r = session.get(url)
            if r.status_code == 200:
                return r.text
            return ''
        except ConnectionError as e:
            if repeat:
                time.sleep(10)
                return self._get_url_content(url, session=session, importer=importer, repeat=False)

    def _get_session(self, importer):
        if self._session:
            return self._session
        session = requests.session()
        params = self._get_params_session(importer)
        url_login = importer.get_url_login_parent()
        session.params = params
        session.headers = {'User-Agent':self._get_agent_browser(importer)}
        if params:
            session.post(url=url_login, data=params)
        if session:
            self._session = session
        return session

    def _get_params_session(self, importer):
        if importer.parent_crawler_id:
            return self._get_params_session(importer.parent_crawler_id)

        dict_params = {}
        if importer.params_login_ids:
            for params in importer.params_login_ids:
                dict_params[params.name] = params.param
        return dict_params

    def _get_agent_browser(self, importer):
        if not importer.agent_browser and importer.parent_crawler_id:
            return self._get_agent_browser(importer.parent_crawler_id)

        if importer.agent_browser:
            return importer.agent_browser

    def _get_product_box_data_expr_ids(self, importer):
        '''
        Method to get the expression to get the data of box product recursevily
        from the importer to the importer first father
        :param importer:
        :return:
        '''
        if not importer.product_box_data_expr_ids and importer.parent_crawler_id:
            return self._get_product_box_data_expr_ids(importer=importer.parent_crawler_id)

        if not importer.product_box_data_expr_ids:
            return None
        return importer.product_box_data_expr_ids

    def _get_next_pagination_url(self, url, session, importer):
        # Get href of products that we need get the data.
        # If there aren't configuration for import hrefs in self, we search in the father recursevily

        if url:
            if not (importer.next_page_expr_href_ids) and importer.parent_crawler_id:
                return self._get_next_pagination_url(url=url, session=session, importer=importer.parent_crawler_id)

            if not importer.parent_crawler_id and not importer.next_page_expr_href_ids:
                raise exceptions.except_orm('Error', 'Pagination expression is not informed (%s)', importer.name)
            else:
                page_content = self.download(url)
                url_base = importer.get_url_parent()
                for get_expression in importer.next_page_expr_href_ids:
                    if get_expression.type_expression == 'xpath':
                        tree_detail = html.fromstring(page_content.content, parser=html.HTMLParser(encoding='utf-8'))
                        try:
                            res_data = tree_detail.xpath(get_expression.expression)
                        except Exception, e:
                            _logger.error("Xpath expression failed (%s, %s)", importer.name, str(get_expression.expression))
                            raise

                        if res_data:
                            next_url = res_data[0]
                            if isinstance(next_url, str):
                                if url_base not in next_url and '://' not in next_url:
                                    return url_base + (next_url if next_url[:1] == '/' else '/' + next_url)
                                else:
                                    return next_url

                    elif get_expression.type_expression == 'regexp':
                        res_data = re.findall(get_expression.expression, page_content.content)
                        if res_data:
                            return res_data[0]

                return None
        return []

    def _get_expression_result(self, expressions, page_detail):
        result = ''
        if expressions:
            try:
                for expression in expressions:
                    result = WebCrawlerAPI.execute_get_expression(expression=expression, page_detail=page_detail)
                    if result:
                        break
                return result
            except Exception, e:
                _logger("Error", str(e))
                return ''

    def _get_search_expression_from_importer(self, name, importer):
        expression = None
        if name == 'sku':
            expression = importer.sku_expr_ids
        elif name == 'name':
            expression = importer.name_expr_ids
        elif name == 'image':
            expression = importer.url_image_expr_ids
        elif name == 'price':
            expression = importer.price_expr_ids
        elif name == 'stock':
            expression = importer.stock_expr_ids
        elif name == 'description':
            expression = importer.short_description_expr_ids
        elif name == 'ean':
            expression = importer.ean_expr_ids
        elif name == 'brand':
            expression = importer.brand_expr_ids
        elif name == 'height':
            expression = importer.height_expr_ids
        elif name == 'length':
            expression = importer.length_expr_ids
        elif name == 'weight':
            expression = importer.weight_expr_ids
        elif name == 'width':
            expression = importer.width_expr_ids
        elif name == 'min_qty':
            expression = importer.min_qty_expr_ids

        if not expression and importer.parent_crawler_id:
            return self._get_search_expression_from_importer(name, importer.parent_crawler_id)

        return expression

    def _get_detail_product_from_page(self, page_html, importer):
        # If the webcrawler hasn't expressions to get data, we go to father to get the expressions
        searched_sku = self._get_expression_result(expressions=self._get_search_expression_from_importer('sku', importer),
                                                   page_detail=page_html)
        searched_name = self._get_expression_result(expressions=self._get_search_expression_from_importer('name', importer),
                                                    page_detail=page_html)
        searched_image = self._get_expression_result(expressions=self._get_search_expression_from_importer('image', importer),
                                                     page_detail=page_html)
        searched_price = self._get_expression_result(expressions=self._get_search_expression_from_importer('price', importer),
                                                     page_detail=page_html)
        searched_stock = self._get_expression_result(expressions=self._get_search_expression_from_importer('stock', importer),
                                                     page_detail=page_html)
        searched_decription = self._get_expression_result(expressions=self._get_search_expression_from_importer('description', importer),
                                                          page_detail=page_html)
        searched_ean = self._get_expression_result(expressions=self._get_search_expression_from_importer('ean', importer),
                                                   page_detail=page_html)
        searched_brand = self._get_expression_result(expressions=self._get_search_expression_from_importer('brand', importer),
                                                     page_detail=page_html)
        searched_height = self._get_expression_result(expressions=self._get_search_expression_from_importer('height', importer),
                                                      page_detail=page_html)
        searched_length = self._get_expression_result(expressions=self._get_search_expression_from_importer('length', importer),
                                                      page_detail=page_html)
        searched_weight = self._get_expression_result(expressions=self._get_search_expression_from_importer('weight', importer),
                                                      page_detail=page_html)
        searched_width = self._get_expression_result(expressions=self._get_search_expression_from_importer('width', importer),
                                                     page_detail=page_html)
        searched_min_qty = self._get_expression_result(expressions=self._get_search_expression_from_importer('min_qty', importer),
                                                       page_detail=page_html)

        prod = {}

        if searched_sku and searched_name:

            prod['sku'] = searched_sku[0]
            prod['name'] = searched_name[0]

            if searched_decription:
                prod['description'] = searched_decription[0]

            if searched_price and searched_price[0]:
                prod['price'] = searched_price[0]
                prod['tax_included'] = importer.get_taxes_included()

            if searched_image:

                image_list = []
                for url_image in searched_image:
                    url_base = importer.get_url_image() or importer.get_url_parent()
                    if url_base not in url_image and '://' not in url_image:
                        url_image = url_base + (url_image if url_image[:1] == '/' else '/' + url_image)

                    image_list.append(url_image)
                prod['urls_image'] = image_list

            if searched_ean:
                prod['ean'] = searched_ean[0]

            prod['supplier_qty'] = 0
            if searched_stock:
                type_stock = self._get_field_from_parents(importer, 'type_stock')
                if type_stock == 'exist' and searched_stock[0]:
                    prod['supplier_qty'] = 3
                elif type_stock == 'units' and searched_stock[0]:
                    prod['supplier_qty'] = searched_stock[0]

            if searched_brand:
                prod['brand'] = searched_brand[0]
            if searched_height:
                prod['height'] = searched_height[0]
            if searched_weight:
                prod['weight'] = searched_weight[0]
            if searched_length:
                prod['length'] = searched_length[0]
            if searched_width:
                prod['width'] = searched_width[0]

            if not searched_min_qty:
                prod['min_qty'] = 1
            else:
                prod['min_qty'] = searched_min_qty[0]

            prod['currency_id'] = self._get_field_from_parents(importer, 'currency_id')

        return prod

    def _get_product_data_by_href(self, importer, url, session=None):
        # We go around href products and download the page to get data
        if not session:
            session = self._get_session(importer)
        html_page = self._get_url_content(url=url, session=session, importer=importer)
        if html_page:
            prod = self._get_detail_product_from_page(page_html=html_page, importer=importer)
            if prod:
                prod['url_product'] = url
                return prod

        return {}

    def _get_field_product_by_href(self, field, importer, session=None):
        '''
        We go around href products and download the page to get data
        :param field: Name of field to recover
        :param importer: object importer
        :param url: Url to recover the field
        :param session: Session to get the html of the url (this isn't mandatory)
        :return:
        '''

        hrefs = self._get_hrefs_product_from_box(importer.url, importer)
        if not hrefs:
            raise exceptions.except_orm('Error', 'There aren\'t hrefs of product to get field %s' % importer.url)

        html_page = self._get_url_content(url=hrefs[0][1], session=session, importer=importer)
        if html_page:
            field_data = self._get_expression_result(expressions=self._get_search_expression_from_importer(field, importer),
                                                     page_detail=html_page)
            return field_data

        return None

    def _get_hrefs_product_from_box(self, url, importer):
        # Get href of products that we need get the data.
        # If there aren't configuration for import hrefs in self, we search in the father recursevily
        if url:

            dict_href = {}

            if importer.get_products:

                box_expressions = importer.product_box_data_expr_ids
                if not box_expressions and importer.parent_crawler_id:
                    box_expressions = self._get_product_box_data_expr_ids(importer)

                page_content = self.download(url)
                url_base = importer.get_url_parent()
                if page_content and box_expressions:
                    for get_expression in box_expressions:
                        if get_expression.type_expression == 'xpath':
                            tree_detail = html.fromstring(page_content.content, parser=html.HTMLParser(encoding='utf-8'))
                            try:
                                res_data = tree_detail.xpath(get_expression.expression)
                            except Exception, e:
                                raise exceptions.except_orm('Error',
                                                            'Hay que echar un ojo a la expresión xpath para los bloques de los productos: ' +
                                                            str(get_expression.expression) +
                                                            '\\n Ha generado el siguiente error: ' + str(e.message))
                            if res_data:
                                for url in res_data:
                                    if url_base[url_base.find('://') + 3 if url_base.find('://') else 0:] in url:
                                        dict_href[url] = (importer, url)
                                    else:
                                        final_url = url_base + (url if url[:1] == '/' else '/' + url)
                                        dict_href[final_url] = ((importer, final_url))

                        elif get_expression.type_expression == 'regexp':
                            try:
                                res_data = re.findall(get_expression.expression, page_content.content)
                            except Exception, e:
                                raise exceptions.except_orm('Error',
                                                            'Hay que echar un ojo a la expresión regular para los bloques de los productos: ' +
                                                            str(get_expression.expression) +
                                                            '\\n Ha generado el siguiente error: ' + str(e.message))
                            if res_data:
                                dict_href[res_data] = (importer, res_data)

                return dict_href
            return {}

    def _get_hrefs_product_from_web(self, importer, url, session):
        list_href_products = []

        try:
            if importer.has_pagination:
                next_url = self._get_next_pagination_url(url=url, session=session, importer=importer)
                if next_url and next_url and next_url not in self._urls_to_get_href_product:
                    self._urls_to_get_href_product.append(next_url)
                    list_href_products.extend(self._get_hrefs_product_from_web(importer=importer, url=next_url, session=session))

            dict_urls = self._get_hrefs_product_from_box(url, importer)

            for element in list_href_products:
                dict_urls.pop(element[1], None)

            for key, value in dict_urls.iteritems():
                list_href_products.append(value)

            return list_href_products
        except Exception as e:
            _logger.error("Error %s" % e.message)
            return list_href_products

    def _get_href_products(self, importer=None, session=None):
        '''
        This method is called from importer.supplier model to get the data from the web
        and insert it into our odoo database instance.
        :return: list of products that we need to insert
        '''
        if not importer:
            importer = self._importer.importer_web_id

        if not session:
            session = self._session if self._session else self._get_session(importer)

        list_hrefs_product = []

        # We throw the recursevely call from the childs webs for example:
        #   supplier.com
        #   suplier.com/catergorie_1.html
        #   suplier.com/catergorie_2.html
        if importer.child_crawler_ids:
            for child in importer.child_crawler_ids:
                new_list = self._get_href_products(importer=child, session=session)
                for item in new_list:
                    if item not in list_hrefs_product:
                        list_hrefs_product.append(item)

        # We get the data from the url that we are processing
        new_list = self._get_hrefs_product_from_web(importer=importer, url=importer.url, session=session)
        if new_list:
            list_hrefs_product.extend(new_list)

        return list_hrefs_product


class SupplierCRUDAdapter(AbstractComponent):
    """ External Records Adapter for Supplier """

    _name = 'supplier.crud.adapter'
    _inherit = ['base.backend.adapter', 'base.supplier.connector']
    _usage = 'backend.adapter'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def _call(self, method, arguments):
        try:
            supplier_api = getattr(self.work, 'supplier_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a supplier_api attribute with a '
                'SupplierAPI instance to be able to use the '
                'Backend Adapter.'
            )
        return supplier_api.call(method, arguments)


class GenericAdapter(AbstractComponent):
    _name = 'supplier.adapter'
    _inherit = 'supplier.crud.adapter'

    _supplier_model = None
    _admin_path = None

    def _get_model(self):
        if self._supplier_model:
            return self._supplier_model
        elif self.model:
            return self.model._name
        elif self._apply_on:
            return self._apply_on
        return ''

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        return self._call('%s_search' % self._get_model(),
                          [filters] if filters else [{}])

    def read(self, external_id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        arguments = [external_id]
        if attributes:
            arguments.append(attributes)
        return self._call('%s_read' % self._get_model().replace('.', '_'), [arguments])

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        return self._call('%s_list' % self._get_model(), [filters])

    def create(self, data):
        """ Create a record on the external system """
        return self._call('%s_create' % self._get_model(), [data])

    def write(self, id, data):
        """ Update records on the external system """
        return self._call('%s_update' % self._get_model(),
                          [int(id), data])

    def delete(self, id):
        """ Delete a record on the external system """
        return self._call('%s.delete' % self._get_model(), [int(id)])
