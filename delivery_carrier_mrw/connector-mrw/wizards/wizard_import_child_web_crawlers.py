# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from lxml import html
from lxml.html import HtmlElement
from requests import Response
from odoo import api, models, exceptions
from ..components.backend_adapter import WebCrawlerAPI


class WizardImportChildCrawlers(models.TransientModel):
    _name = "supplier.import.child.crawlers.wizard"
    _description = "Import Child Crawlers Wizard"

    @api.multi
    def check_import_web_crawlers(self):
        web_importer = self.env['importer.supplier.webcrawler'].browse(self._context.get('active_ids', []))
        url_names = self._get_url_and_names_childs(web_importer)
        self._show_child_crawlers(url_names)

    @api.multi
    def import_web_crawlers(self):
        web_importer = self.env['importer.supplier.webcrawler'].browse(self._context.get('active_ids', []))
        url_names = self._get_url_and_names_childs(web_importer)
        self._write_child_crawlers(web_importer, url_names)

    @api.multi
    def unlink_web_crawlers(self):
        web_importer = self.env['importer.supplier.webcrawler'].browse(self._context.get('active_ids', []))
        for child in web_importer.child_crawler_ids:
            self.delete_web_crawlers(child)

    def delete_web_crawlers(self, web_importer):
        for child in web_importer.child_crawler_ids:
            self.delete_web_crawlers(child)
        web_importer.unlink()

    @api.multi
    def _get_url_and_names_childs(self, web_importer):
        urls = []
        names = []
        try:
            if web_importer.url:
                tree_detail = None

                try:
                    page_detail = WebCrawlerAPI.download(web_importer.url)

                    if isinstance(page_detail, unicode) or isinstance(page_detail, Response):
                        tree_detail = html.fromstring(page_detail.content,
                                                      parser=html.HTMLParser(encoding='utf-8'))
                    else:
                        tree_detail = html.fromstring(page_detail, parser=html.HTMLParser(encoding='utf-8'))
                except Exception, e:
                    raise exceptions.except_orm('Error',
                                                'There is a error trying to recover the content of the page: \n' + str(
                                                    e.message))

                if tree_detail:
                    # Do a bucle on expression to get childs webcrawler
                    for child_import in web_importer.child_expr_ids:
                        # Recover urls
                        for expr in child_import.url_expr_ids:
                            if expr.type_expression == 'xpath':
                                try:
                                    res_data = tree_detail.xpath(expr.expression)
                                except Exception, e:
                                    raise exceptions.except_orm('Error',
                                                                'The xpath expresion to recover url childs, fail: ' +
                                                                str(expr.expression))
                                url_base = web_importer.get_url_parent()
                                for data in res_data:
                                    if isinstance(data, (str, unicode)):
                                        if url_base in data:
                                            urls.append(data)
                                        else:
                                            urls.append(url_base + (data if data[:1] == '/' else '/' + data))
                                    elif isinstance(data, HtmlElement):
                                        text = data.text
                                        if url_base in text:
                                            urls.append(text)
                                        else:
                                            urls.append(url_base + (text if text[:1] == '/' else '/' + text))

                        # Recover names
                        for expr in child_import.name_expr_ids:
                            if expr.type_expression == 'xpath':
                                try:
                                    res_data = tree_detail.xpath(expr.expression)
                                except Exception, e:
                                    raise exceptions.except_orm('Error',
                                                                'The xpath expresion to recover the name of the childs, fail: ' +
                                                                str(expr.expression))
                                for data in res_data:
                                    if isinstance(data, (str, unicode)):
                                        names.append(data)
                                    elif isinstance(data, HtmlElement):
                                        text = data.text
                                        names.append(text)

                            elif expr.type_expression == 'regexp':
                                try:
                                    res_data = re.findall(expr.expression, tree_detail)
                                except Exception, e:
                                    raise exceptions.except_orm('Error',
                                                                'The regular expresion to recover the name of the childs, fail: ' +
                                                                str(expr.expression))
                                if res_data:
                                    for data in res_data:
                                        names.append(data)
        except Exception, e:
            raise e

        return (urls, names)

    def _write_child_crawlers(self, web_importer, urls_names):
        try:
            urls = urls_names[0]
            names = urls_names[1]
            web_crawler_added = []
            if len(urls) == len(names):
                tam = len(urls)
                i = 0
                while i < tam:
                    url = urls[i]
                    name = names[i]
                    if not name:
                        name = url
                    i += 1
                    if not web_importer.child_crawler_ids:
                        web_importer.write({'child_crawler_ids':[(0, 0, {'name':name,
                                                                         'url':url,
                                                                         'get_products':web_importer.child_expr_ids.child_get_products,
                                                                         'has_pagination':web_importer.child_expr_ids.child_has_pagination, })
                                                                 ]})
                        web_crawler_added.append(name)
                    else:
                        finded = False
                        for child in web_importer.child_crawler_ids:
                            if name in web_crawler_added:
                                finded = True
                        if not finded:
                            web_importer.write({'child_crawler_ids':[(0, 0, {'name':name,
                                                                             'url':url,
                                                                             'get_products':web_importer.child_expr_ids.child_get_products,
                                                                             'has_pagination':web_importer.child_expr_ids.child_has_pagination, })]})
                            web_crawler_added.append(name)

            else:
                for data in urls:
                    if not web_importer.child_crawler_ids:
                        web_importer.write({'child_crawler_ids':[(0, 0, {'name':data,
                                                                         'url':data,
                                                                         'get_products':web_importer.child_expr_ids.child_get_products,
                                                                         'has_pagination':web_importer.child_expr_ids.child_has_pagination,
                                                                         })]})
                        web_crawler_added.append(data)
                    else:
                        finded = False
                        for child in web_importer.child_crawler_ids:
                            if data in web_crawler_added:
                                finded = True
                        if not finded:
                            web_importer.write({'child_crawler_ids':[(0, 0, {'name':data,
                                                                             'url':data,
                                                                             'get_products':web_importer.child_expr_ids.child_get_products,
                                                                             'has_pagination':web_importer.child_expr_ids.child_has_pagination,
                                                                             })]})
                            web_crawler_added.append(data)

            return web_crawler_added
        except Exception, e:
            raise exceptions.except_orm('Error',
                                        'There is a error trying to save the child crawlers: ' +
                                        str(e.message))

    def _show_child_crawlers(self, urls_names):
        urls = urls_names[0]
        names = urls_names[1]
        mes = ''
        if len(urls) == len(names):
            tam = len(urls)
            i = 0
            while i < tam:
                url = urls[i]
                name = names[i]
                if not name:
                    name = url
                i += 1
                mes = mes + name + ' - ' + url + '\n'
            raise exceptions.except_orm('Info',
                                        'This is the relation of names-url recovered: \n%s' % mes)
        else:
            raise exceptions.except_orm('Error',
                                        'There are %d urls and %d names. Check the expression to import these' % (len(urls), len(names)))
