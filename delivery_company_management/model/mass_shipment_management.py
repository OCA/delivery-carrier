# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2019 Halltic eSolutions (http://halltic.com)
#                  Tristán Mozos <tristan.mozos@halltic.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64
import csv

import logging
import os
import shutil
import tempfile
import unicodedata

from contextlib import closing
from pyPdf import PdfFileWriter, PdfFileReader

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


class MassShipmentManagement(models.Model):
    _name = "mass.shipment.management"

    shipment_date = fields.Date('Shipment date', required=True)
    label = fields.Date('Shipment Label')

    state = fields.Selection([
        ('import', 'Import'),
        ('generate', 'Generate'),
        ('confirm', 'Confirm'),
        ('done', 'Done')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='import')

    stock_picking_ids = fields.One2many(comodel_name='mass.shipment.stock.picking',
                                        inverse_name='mass_delivery_id')

    imported_pending_orders = fields.Boolean('Flag pending orders', default=False, help='Flag to mark the import of orders has been done')

    error_message = fields.Char('Error message generating orders')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.shipment_date))
        return result

    def _merge_pdf(self, documents):
        """Merge PDF files into one.

        :param documents: list of path of pdf files
        :returns: path of the merged pdf
        """
        writer = PdfFileWriter()
        streams = []  # We have to close the streams *after* PdfFilWriter's call to write()
        try:
            for document in documents:
                pdfreport = file(document, 'rb')
                streams.append(pdfreport)
                reader = PdfFileReader(pdfreport)
                for page in range(0, reader.getNumPages()):
                    writer.addPage(reader.getPage(page))

            merged_file_fd, merged_file_path = tempfile.mkstemp(suffix='.pdf', prefix='label.tmp.')
            with closing(os.fdopen(merged_file_fd, 'w')) as merged_file:
                writer.write(merged_file)
        finally:
            for stream in streams:
                try:
                    stream.close()
                except Exception:
                    pass

        return merged_file_path

    def _get_carriers(self, amazon_market_product, sale):
        if not sale or not sale.shipment_service_level_category:
            return
        if 'Standard' in sale.shipment_service_level_category:
            delivery_carriers = [template_ship.delivery_standard_carrier_ids for template_ship in
                                 amazon_market_product.product_id.backend_id.shipping_template_ids
                                 if template_ship.name == amazon_market_product.merchant_shipping_group and
                                 template_ship.marketplace_id.id == amazon_market_product.marketplace_id.id]
        else:
            delivery_carriers = [template_ship.delivery_expedited_carrier_ids for template_ship in
                                 amazon_market_product.product_id.backend_id.shipping_template_ids
                                 if template_ship.name == amazon_market_product.merchant_shipping_group and
                                 template_ship.marketplace_id.id == amazon_market_product.marketplace_id.id]

        return delivery_carriers

    def eq_plain(self, s1, s2):

        if s1 == None and s2 == None:
            return True
        elif s1 != None and s2 == None or s1 == None and s2 != None:
            return False

        def normalize(c):
            return unicodedata.normalize("NFD", c)[0].upper()

        return all((normalize(c1) == normalize(c2)) for (c1, c2) in zip(s1, s2))

    def _check_same_reference_task_picking(self, dict_references, picking):
        same_pick = True
        if not dict_references:
            return same_pick
        for move in picking.move_lines:
            if not dict_references.get(move.product_id.default_code) or float(dict_references[move.product_id.default_code]) != move.product_uom_qty:
                same_pick = False
        return same_pick

    def _get_dict_number_ship_reference(self, reference_ship):
        dict_references = {}
        if reference_ship:
            reference_split = reference_ship.split('|')
            for reference in reference_split:
                if not dict_references.get(reference):
                    dict_references[reference] = 1
                else:
                    dict_references[reference] = dict_references[reference] + 1
        return dict_references

    def _get_sale_type_ship_from_task(self, task_name):
        name_split = task_name.split(';')
        type_ship = None
        ship_name = None
        reference_ship = None

        if len(name_split) == 1:
            ship_name = name_split[0]
        elif len(name_split) == 2:
            type_ship = name_split[0]
            ship_name = name_split[1]
        elif len(name_split) == 3:
            type_ship = name_split[0]
            ship_name = name_split[1]
            reference_ship = name_split[2]

        # If we haven't sale or we have two sales with search params we aren't manage the task
        sale = self.env['sale.order'].search(['|', ('name', 'ilike', '%s' % ship_name), ('partner_shipping_id.name', 'ilike', '%s' % ship_name)])

        if len(name_split) == 2 and not sale:
            sale = self.env['sale.order'].search(['|', ('name', 'ilike', '%s' % type_ship), ('partner_shipping_id.name', 'ilike', '%s' % type_ship)])
            if sale:
                reference_ship = ship_name

        dict_references = self._get_dict_number_ship_reference(reference_ship)

        # TODO the first line check we will need to remove when the development has be done
        if not (not type_ship or self.eq_plain(type_ship, u'envio') or self.eq_plain(type_ship, u'reenvio')) or \
                not sale or len(sale) > 1 or not self._check_same_reference_task_picking(dict_references, sale.picking_ids.sorted('create_date')[0]):
            return

        return [type_ship, sale] if sale else None

    def _choose_picking_from_task(self, task_name):

        picking = None

        aux = self._get_sale_type_ship_from_task(task_name)
        if aux:
            type_ship = aux[0]
            sale = aux[1]

            if not type_ship or self.eq_plain(type_ship, u'envio'):
                picking = sale.picking_ids.sorted('create_date')[0] if sale.picking_ids else None
            elif self.eq_plain(type_ship, u'reenvio'):
                picking = sale.picking_ids.sorted('create_date')[0].copy() if sale.picking_ids else None
                picking.action_confirm()
            elif self.eq_plain(type_ship, u'retorno'):
                picking = sale.picking_ids.sorted('create_date')[0].copy() if sale.picking_ids else None
            elif self.eq_plain(type_ship, u'canje'):
                picking = sale.picking_ids.sorted('create_date')[0].copy() if sale.picking_ids else None

            return (picking, sale, type_ship) if picking and sale else None

    def _create_mass_ship_from_task(self, task, carrier_id):
        data = self._choose_picking_from_task(task.name)

        if not data:
            return

        if not carrier_id:
            carrier_id = self._choose_carrier(data[0], data[1]) or self.env['delivery.carrier'].browse(1)

        if not data[0].id in self.stock_picking_ids.mapped('stock_picking_id').mapped('id'):
            type_ship = '0'
            if self.eq_plain(data[2], u'reenvio'):
                type_ship = '3'
            elif self.eq_plain(data[2], u'canje'):
                type_ship = '1'
            elif self.eq_plain(data[2], u'retorno'):
                type_ship = '2'

            vals = {'mass_delivery_id':self.id,
                    'stock_picking_id':data[0].id,
                    'type_ship':type_ship,
                    'sale_order_id':data[1].id,
                    'delivery_carrier_id':carrier_id.id,
                    'task_id':task.id
                    }
            return self.env['mass.shipment.stock.picking'].create(vals)
        else:
            stock_picking = self.stock_picking_ids.filtered(lambda x:x.stock_picking_id.id == data[0].id and x.mass_delivery_id.id == self.id)
            stock_picking.task_id = task.id

    def _move_pending_stock_task(self):
        tasks = self.env['project.task'].search([('project_id.name', '=', 'Gesti\xf3n env\xedos'), ('stage_id.name', 'ilike', 'Pendientes de stock')])
        for task in tasks:
            data = self._get_sale_type_ship_from_task(task.name)
            if data:
                move_task = True
                picking = data[1].picking_ids.sorted('create_date')[0]
                for move in picking.move_lines:
                    if move.ordered_qty > move.product_id.qty_available:
                        move_task = False

                if move_task and data[1].amazon_bind_ids:
                    self._choose_carrier_amazon_sale(picking, data[1])
                    if picking.carrier_id and picking.carrier_id.carrier_type == 'correos':
                        task.stage_id = self.env['project.task.type'].search([('name', '=', 'Pendiente Correos'),
                                                                              ('project_ids.name', '=', 'Gesti\xf3n env\xedos')]).id
                    elif picking.carrier_id and picking.carrier_id.carrier_type == 'mrw':
                        task.stage_id = self.env['project.task.type'].search([('name', '=', 'Pendiente MRW'),
                                                                              ('project_ids.name', '=', 'Gesti\xf3n env\xedos')]).id
                    elif picking.carrier_id and picking.carrier_id.carrier_type == 'spring':
                        task.stage_id = self.env['project.task.type'].search([('name', '=', 'Pendiente Spring'),
                                                                              ('project_ids.name', '=', 'Gesti\xf3n env\xedos')]).id

    def _get_pending_orders_from_projects(self):
        task_ids = self.stock_picking_ids.mapped('task_id').mapped('id')
        tasks = self.env['project.task'].search([('project_id.name', '=', 'Gesti\xf3n env\xedos'),
                                                 ('stage_id.name', 'ilike', 'Pendiente MRW'),
                                                 ('id', 'not in', task_ids)])
        carrier_id = self.env['delivery.carrier'].search([('name', '=', 'MRW ecommerce Nacional')])
        for task in tasks:
            try:
                self._create_mass_ship_from_task(task, carrier_id)
            except Exception as e:
                _logger = logging.getLogger(e.message)

        carrier_id = None
        task_ids = self.stock_picking_ids.mapped('task_id').mapped('id')
        tasks = self.env['project.task'].search([('project_id.name', '=', 'Gesti\xf3n env\xedos'),
                                                 ('stage_id.name', 'ilike', 'Pendiente Spring'),
                                                 ('id', 'not in', task_ids)])
        for task in tasks:
            try:
                self._create_mass_ship_from_task(task, carrier_id)
            except Exception as e:
                _logger = logging.getLogger(e.message)

        task_ids = self.stock_picking_ids.mapped('task_id').mapped('id')
        tasks = self.env['project.task'].search([('project_id.name', '=', 'Gesti\xf3n env\xedos'),
                                                 ('stage_id.name', 'ilike', 'Pendiente Correos'),
                                                 ('id', 'not in', task_ids)])
        carrier_id = self.env['delivery.carrier'].search([('name', '=', 'Correos Ordinario Nacional')])
        for task in tasks:
            try:
                self._create_mass_ship_from_task(task, carrier_id)
            except Exception as e:
                _logger = logging.getLogger(e.message)

        return

    def get_orders_from_project(self):
        try:
            self._move_pending_stock_task()
        except Exception as e:
            _logger = logging.getLogger(e.message)

        try:
            self._get_pending_orders_from_projects()
        except Exception as e:
            _logger = logging.getLogger(e.message)

        return

    def get_pending_orders(self):
        pickings = self.env['stock.picking'].search(
            [('state', 'in', ('assigned', 'confirmed')),
             ('picking_type_code', '=', 'outgoing'),
             ('id', 'not in', self.stock_picking_ids.mapped('stock_picking_id').ids)])

        for picking in pickings:
            add_sale = True
            delivery_carrier_id = None
            sale = self.env['sale.order'].search([('name', '=', picking.origin)])
            if sale and sale.amazon_bind_ids:

                # If the sale not is Unshipped the order isn't processed
                if sale.amazon_bind_ids.order_status_id.name == 'Shipped' and picking.state != 'done':
                    picking.action_done()

                if sale.amazon_bind_ids.order_status_id.name != 'Unshipped':
                    add_sale = False
                else:
                    # Recover the shipping template of the sale and with this we are going to calculate the service to use for ship
                    self._choose_carrier_amazon_sale(picking, sale)

            delivery_carrier_id = self._choose_carrier(picking, sale) or self.env['delivery.carrier'].browse(1)

            if add_sale:
                self.write({'stock_picking_ids':[(0, 0, {'stock_picking_id':picking.id,
                                                         'type_ship':'0',
                                                         'sale_order_id':sale.id,
                                                         'delivery_carrier_id':delivery_carrier_id.id,
                                                         })
                                                 ]})

        self.get_orders_from_project()
        self.state = 'generate'
        return

    def add_issue_orders(self):
        return

    def _generate_mrw_order(self, order):
        try:
            # If we haven't a tracking of the carrier we must to generate one
            if not order.is_done:
                order.stock_picking_id.min_date = self.shipment_date
                order.stock_picking_id.carrier_id = order.delivery_carrier_id
                if order.type_ship in ('0', '3'):
                    order.stock_picking_id.mrw_service_type = '0800'
                elif order.type_ship == '1':
                    order.stock_picking_id.mrw_service_type = '0810'
                order.stock_picking_id.action_generate_carrier_label()

            # When we have a tracking number we validate the picking
            if order.stock_picking_id.carrier_tracking_ref:
                order.stock_picking_id.action_done()
                order.is_done = True
                order.error_message = None
        except UserError as e:
            order.error_message = e.name
        except Exception as e:
            order.error_message = e.message

    def _generate_correos_order(self, order):
        order.stock_picking_id.carrier_id = order.delivery_carrier_id
        order.stock_picking_id.action_done()
        order.is_done = True

    def _generate_correos_cert_order(self, order):
        order.is_done = True

    def _generate_spring_order(self, order):
        try:
            if not order.stock_picking_id.carrier_tracking_ref:
                order.stock_picking_id.min_date = self.shipment_date
                order.stock_picking_id.carrier_id = order.delivery_carrier_id
                if order.type_ship in ('0', '3'):
                    order.stock_picking_id.spring_service_type = order.delivery_carrier_id.code
                try:
                    order.stock_picking_id.action_generate_carrier_label()
                except UserError as e:
                    if e.name == 'This Shipper Reference already exists':
                        # Get the last label
                        order.stock_picking_id.generate_labels(package_ids=order.stock_picking_id.name)

            # When we have a tracking number we validate the picking
            if order.stock_picking_id.carrier_tracking_ref:
                order.stock_picking_id.action_done()
                order.is_done = True
                order.error_message = None
        except UserError as e:
            order.error_message = e.name
        except Exception as e:
            order.error_message = e.name

    def _generate_mrw_labels(self):
        try:
            self.env['ir.attachment'].search([('res_model', '=', self._name), ('res_id', '=', self.id), ('name', 'ilike', 'mrw')]).unlink()
            with tools.osutil.tempdir() as path_temp_dir:
                filestore_path = self.env['ir.attachment']._filestore()

                path_list = []
                for pick in self.stock_picking_ids:
                    if pick.is_done and pick.stock_picking_id.carrier_id and 'mrw' in pick.stock_picking_id.carrier_id.carrier_type:
                        # We get only the last label that we had generated
                        attachments = self.env['ir.attachment'].search([('res_id', '=', pick.stock_picking_id.id), ('res_model', '=', 'stock.picking')],
                                                                       order='id DESC',
                                                                       limit=1)
                        for attachment in attachments:
                            if attachment.store_fname:
                                shutil.copy2('%s/%s' % (filestore_path, attachment.store_fname), path_temp_dir)
                                path_list.append('%s/%s' % (path_temp_dir, attachment.checksum))

                if path_list:
                    mergue_file_path = self._merge_pdf(path_list)
                    attachment_vals = {
                        'name':'%s_%s' % (self.shipment_date, 'mrw_labels.pdf'),
                        'datas':base64.b64encode(open(mergue_file_path, "rb").read()),
                        'datas_fname':'%s_%s' % (self.shipment_date, 'mrw_labels.pdf'),
                        'res_model':self._name,
                        'res_id':self.id,
                    }
                    self.env['ir.attachment'].create(attachment_vals)
        except Exception as e:
            self.error_message = e.message

    def _generate_spring_labels(self):
        try:
            self.env['ir.attachment'].search([('res_model', '=', self._name), ('res_id', '=', self.id), ('name', 'ilike', 'spring')]).unlink()
            with tools.osutil.tempdir() as path_temp_dir:
                filestore_path = self.env['ir.attachment']._filestore()

                path_list = []
                for pick in self.stock_picking_ids:
                    if pick.is_done and pick.stock_picking_id.carrier_id and 'spring' in pick.stock_picking_id.carrier_id.carrier_type:
                        attachments = self.env['ir.attachment'].search([('res_id', '=', pick.stock_picking_id.id), ('res_model', '=', 'stock.picking')],
                                                                       order='id DESC',
                                                                       limit=1)
                        for attachment in attachments:
                            if attachment.store_fname:
                                shutil.copy2('%s/%s' % (filestore_path, attachment.store_fname), path_temp_dir)
                                path_list.append('%s/%s' % (path_temp_dir, attachment.checksum))

                if path_list:
                    mergue_file_path = self._merge_pdf(path_list)
                    attachment_vals = {
                        'name':'%s_%s' % (self.shipment_date, 'spring_labels.pdf'),
                        'datas':base64.b64encode(open(mergue_file_path, "rb").read()),
                        'datas_fname':'%s_%s' % (self.shipment_date, 'spring_labels.pdf'),
                        'res_model':self._name,
                        'res_id':self.id,
                    }
                    self.env['ir.attachment'].create(attachment_vals)
        except Exception as e:
            self.error_message = e.message

    def _generate_correos_labels(self):
        try:
            self.env['ir.attachment'].search([('res_model', '=', self._name), ('res_id', '=', self.id), ('name', 'ilike', 'correos')]).unlink()
            filas_csv = []
            for stock_piking in self.stock_picking_ids:
                if stock_piking.delivery_carrier_id.carrier_type == 'correos' and stock_piking.is_done:
                    fila = [stock_piking.stock_picking_id.partner_id.name.encode('utf-8', 'ignore'),
                            ('%s %s' % (stock_piking.stock_picking_id.partner_id.street, stock_piking.stock_picking_id.partner_id.street2 or '')).encode(
                                'utf-8',
                                'ignore'),
                            ('%s %s' % (stock_piking.stock_picking_id.partner_id.zip, stock_piking.stock_picking_id.partner_id.city)).encode('utf-8', 'ignore'),
                            'Ref: ' + stock_piking.ship_reference]
                    filas_csv.append(fila)

            if filas_csv:
                with tools.osutil.tempdir() as path_temp_dir:
                    myf = open('%s/temp.csv' % path_temp_dir, 'w+')
                    writer = csv.writer(myf, delimiter=',', lineterminator='\n')
                    for row in filas_csv:
                        writer.writerow(row)
                    myf.close()

                    attachment_vals = {
                        'name':'%s_%s' % (self.shipment_date, 'correos_labels.csv'),
                        'datas':base64.b64encode(open('%s/temp.csv' % path_temp_dir, "rb").read()),
                        'datas_fname':'%s_%s' % (self.shipment_date, 'correos_labels.csv'),
                        'res_model':self._name,
                        'res_id':self.id,
                    }
                    self.env['ir.attachment'].create(attachment_vals)
        except Exception as e:
            self.error_message = e.message

        return

    def _generate_manifest_reference_count(self):
        try:
            self.env['ir.attachment'].search(['&', ('res_model', '=', self._name),
                                              ('res_id', '=', self.id),
                                              '|',
                                              ('name', 'ilike', 'manifest'),
                                              ('name', 'ilike', 'reference_count')]).unlink()

            ship_stock_pick = self.env['mass.shipment.stock.picking'].search([('mass_delivery_id', '=', self.id), ('is_done', '=', True)]).sorted(
                'ship_reference').sorted('delivery_carrier_type')
            with tools.osutil.tempdir() as path_temp_dir:
                manifest_file = open('%s/manifest.txt' % path_temp_dir, 'w+')
                reference_count_file = open('%s/reference_count.txt' % path_temp_dir, 'w+')
                carrier = None
                reference = None
                reference_count = 0
                for order_done in ship_stock_pick:
                    # Count the references
                    if not reference:
                        reference = order_done.ship_reference

                    if not carrier or carrier != order_done.delivery_carrier_id.carrier_type:
                        carrier = order_done.delivery_carrier_id.carrier_type
                        carrier_title = '-------------------------------- %s --------------------------------\n' % order_done.delivery_carrier_id.carrier_type.capitalize()
                        manifest_file.write(carrier_title)
                        if reference_count != 0:
                            # if the carrier change, the count of reference change too
                            reference_count_file.write('%s of %s \n' % (reference_count, reference))
                            reference = order_done.ship_reference
                        reference_count = 1
                        reference_count_file.write(carrier_title)

                    elif reference != order_done.ship_reference:
                        reference_count_file.write('%s of %s \n' % (reference_count, reference))
                        reference = order_done.ship_reference
                        reference_count = 1
                    else:
                        reference_count += 1

                    ship_reference = order_done.stock_picking_id.carrier_tracking_ref or order_done.stock_picking_id.name
                    row = ('%s %s %s %s\n' % (order_done.delivery_carrier_id.carrier_type,
                                              ship_reference,
                                              order_done.stock_picking_id.partner_id.name,
                                              order_done.ship_reference)).encode('utf-8', 'ignore')
                    manifest_file.write(row)

                    if order_done.task_id:
                        self._move_orders_to_send_task(order_done.task_id)

                reference_count_file.write('%s of %s \n' % (reference_count, reference))
                manifest_file.close()
                reference_count_file.close()
                attachment_vals = {
                    'name':'%s_%s' % (self.shipment_date, 'manifest.txt'),
                    'datas':base64.b64encode(open('%s/manifest.txt' % path_temp_dir, "rb").read()),
                    'datas_fname':'%s_%s' % (self.shipment_date, 'manifest.txt'),
                    'res_model':self._name,
                    'res_id':self.id,
                }
                self.env['ir.attachment'].create(attachment_vals)
                attachment_vals = {
                    'name':'%s_%s' % (self.shipment_date, 'reference_count.txt'),
                    'datas':base64.b64encode(open('%s/reference_count.txt' % path_temp_dir, "rb").read()),
                    'datas_fname':'%s_%s' % (self.shipment_date, 'reference_count.txt'),
                    'res_model':self._name,
                    'res_id':self.id,
                }
                self.env['ir.attachment'].create(attachment_vals)

        except Exception as e:
            self.error_message = e.message

    def _move_orders_to_send_task(self, task):
        task.stage_id = self.env['project.task.type'].search([('name', '=', 'Enviado'),
                                                              ('project_ids.name', '=', 'Gesti\xf3n env\xedos')]).id
        issue = self.env['project.issue'].search([('task_id', '=', task.id)])
        if issue:
            issue.stage_id = self.env['project.task.type'].search([('name', '=', 'Pedido reenviado'),
                                                                   ('project_ids.name', 'ilike', 'Incidencias de pedidos')]).id
        return

    def _choose_carrier_amazon_sale(self, picking, sale):
        for line in sale.amazon_bind_ids.amazon_order_line_ids:
            detail_product = line.get_amazon_detail_product()
            carriers = self._get_carriers(detail_product, sale.amazon_bind_ids)
            if carriers:
                for carrier in carriers[0]:
                    # If there are several items and one of these is not equal that "correos" we are going to choose this
                    if carrier.verify_carrier(picking.partner_id) and \
                            (not picking.carrier_id or (picking.carrier_id and picking.carrier_id.carrier_type == 'correos')):
                        picking.carrier_id = carrier

    def _choose_carrier(self, picking, sale):
        delivery_carrier_id = None
        country = picking.partner_id.country_id
        zip = picking.partner_id.zip

        if not country or not zip:
            return

        # If the order is from Canary islands or Melilla or Ceuta
        if country.code == 'ES' and (zip[0:2] == '35' or zip[0:2] == '38' or zip[0:2] == '51' or zip[0:2] == '52'):
            delivery_carrier_id = self.env['delivery.carrier'].search([('name', '=', 'Correos Certificado Nacional')])
        elif 'spring' == picking.carrier_id.carrier_type and (country.code == 'ES' or country.code == 'PT'):
            delivery_carrier_id = self.env['delivery.carrier'].search([('name', '=', 'MRW ecommerce Nacional')])
        elif ('spring' == picking.carrier_id.carrier_type or 'mrw' == picking.carrier_id.carrier_type) and (country.code != 'ES' and country.code != 'PT'):
            carrier_name = 'Spring %s %s'

            if sale.amount_untaxed > 60:
                carrier_name = carrier_name % (country.name, 'Signed')
            else:
                carrier_name = carrier_name % (country.name, 'Tracked')

            delivery_carrier_id = self.env['delivery.carrier'].search([('name', '=', carrier_name)])

        return delivery_carrier_id or picking.carrier_id

    def generate_order_carrier(self, order):
        if order.delivery_carrier_id.carrier_type == 'correos':
            self._generate_correos_order(order)
        elif order.delivery_carrier_id.carrier_type == 'mrw':
            self._generate_mrw_order(order)
        elif order.delivery_carrier_id.carrier_type == 'spring':
            self._generate_spring_order(order)

    def generate_orders(self):
        self.error_message = None
        for order in self.stock_picking_ids:
            if not order.is_done:
                self.generate_order_carrier(order)

        self._generate_mrw_labels()
        self._generate_spring_labels()
        self._generate_correos_labels()
        self._generate_manifest_reference_count()
        self.state = 'confirm'
        return

    def _confirm_orders_on_amazon(self):
        try:
            self.env['ir.attachment'].search(['&', ('res_model', '=', self._name),
                                              ('res_id', '=', self.id),
                                              ('name', 'ilike', 'amazon_confirmation_orders')]).unlink()

            ship_stock_pick = self.stock_picking_ids.filtered('is_done')
            with tools.osutil.tempdir() as path_temp_dir:
                myf = open('%s/amazon_confirmation_orders.csv' % path_temp_dir, 'w+')
                writer = csv.writer(myf, delimiter='\t', lineterminator='\n')
                writer.writerow(['order-id', 'order-item-id', 'quantity', 'ship-date', 'carrier-code', 'carrier-name', 'tracking-number', 'ship-method'])
                for order_done in ship_stock_pick:
                    if order_done.sale_order_id.amazon_bind_ids:
                        for amazon_order_line in order_done.sale_order_id.amazon_bind_ids.amazon_order_line_ids:
                            carrier_name = None
                            if order_done.delivery_carrier_id.carrier_type == 'mrw':
                                carrier_name = 'MRW'
                            elif order_done.delivery_carrier_id.carrier_type == 'correos':
                                carrier_name = 'Correos'
                            elif order_done.delivery_carrier_id.carrier_type == 'spring':
                                if not order_done.stock_picking_id.sub_carrier:
                                    carrier_name = 'Spring'
                                elif 'PostNL' in order_done.stock_picking_id.sub_carrier:
                                    carrier_name = 'Post NL'
                                elif 'Hermes' in order_done.stock_picking_id.sub_carrier:
                                    carrier_name = 'Hermes Logistik Gruppe'
                                elif 'Italian Post Crono' in order_done.stock_picking_id.sub_carrier:
                                    carrier_name = 'Chronopost'
                                elif 'Colis Prive' in order_done.stock_picking_id.sub_carrier:
                                    carrier_name = 'Colis Prive'
                                elif 'Royal Mail' in order_done.stock_picking_id.sub_carrier:
                                    carrier_name = 'Royal Mail'

                            row = [amazon_order_line.amazon_order_id.id_amazon_order,
                                   amazon_order_line.id_item,
                                   amazon_order_line.qty_ordered,
                                   self.shipment_date,
                                   '',
                                   carrier_name,
                                   order_done.stock_picking_id.sub_carrier_tracking_ref or order_done.stock_picking_id.carrier_tracking_ref or '',
                                   ''
                                   ]

                            # TODO export automatically the confirmation on Amazon
                            """
                            exporter_product = work.component(model_name='amazon.product.product', usage='amazon.product.export')
                            ids = exporter_product.run(add_products_to_inventory)
                            """

                            writer.writerow(row)
                myf.close()

                attachment_vals = {
                    'name':'%s_%s' % (self.shipment_date, 'amazon_confirmation_orders.csv'),
                    'datas':base64.b64encode(open('%s/amazon_confirmation_orders.csv' % path_temp_dir, "rb").read()),
                    'datas_fname':'%s_%s' % (self.shipment_date, 'amazon_confirmation_orders.csv'),
                    'res_model':self._name,
                    'res_id':self.id,
                }
                self.env['ir.attachment'].create(attachment_vals)
        except Exception as e:
            self.error_message = e.message

    def confirm_orders_on_marketplaces(self):
        self._confirm_orders_on_amazon()
        return


class SaleOrderToSend(models.Model):
    _name = "mass.shipment.stock.picking"

    mass_delivery_id = fields.Many2one('mass.delivery', ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', strore=True, compute='_onchange_sale_order_id')
    stock_picking_id = fields.Many2one('stock.picking', required=True)
    picking_state = fields.Char('Picking state', compute='_compute_state')
    customer_name = fields.Char('Customer name', related='stock_picking_id.partner_id.name')
    country_customer_name = fields.Char('Customer country', related='stock_picking_id.partner_id.country_id.name')
    type_ship = fields.Selection(selection=[('0', 'First ship'),
                                            ('1', 'Change'),
                                            ('2', 'Return'),
                                            ('3', 'Re-send'), ], required=True)
    delivery_carrier_id = fields.Many2one('delivery.carrier', required=True)
    delivery_carrier_name = fields.Char('Delivery Carrier', related='delivery_carrier_id.name')
    delivery_carrier_type = fields.Char('Delivery Carrier', compute='_compute_delivery_type')
    ship_reference = fields.Char('Order Reference', strore=True, compute='_onchange_ship_reference')
    limit_ship_date = fields.Date('Date limit', strore=True, compute='_compute_date_limit')
    margin = fields.Date('Margen', strore=True, compute='_onchange_margin')
    is_done = fields.Boolean(default=False)
    error_message = fields.Char('Error message', readonly=True)
    resend_created = fields.Boolean(default=False)
    is_confirmed = fields.Boolean(default=False)
    task_id = fields.Many2one('project.task')

    @api.one
    def _compute_date_limit(self):
        for mass_ship in self:
            if mass_ship.sale_order_id.amazon_bind_ids:
                mass_ship.limit_ship_date = mass_ship.sale_order_id.amazon_bind_ids.date_latest_ship
            else:
                mass_ship.limit_ship_date = mass_ship.sale_order_id.commitment_date

    @api.one
    def _compute_delivery_type(self):
        for mass_ship in self:
            mass_ship.delivery_carrier_type = mass_ship.delivery_carrier_id.carrier_type

    @api.one
    def _compute_state(self):
        for mass_ship in self:
            mass_ship.picking_state = dict(mass_ship.stock_picking_id._fields['state'].selection).get(mass_ship.stock_picking_id.state)

    @api.onchange('stock_picking_id')
    def _onchange_sale_order_id(self):
        for picking in self:
            picking.sale_order_id = self.env['sale.order'].search([('name', '=', picking.stock_picking_id.origin)]).id

    @api.onchange('stock_picking_id')
    def _onchange_ship_reference(self):
        for picking in self:
            picking.ship_reference = picking.stock_picking_id._get_ship_reference()

    @api.onchange('stock_picking_id')
    def _onchange_margin(self):
        for picking in self:
            picking.margin = 0

    @api.model
    def create(self, vals):
        # if vals.get('type_ship') == '3' and not self.resend_created:
        # res = self.copy()
        # TODO create new stock.picking
        # res.resend_created = True
        vals['ship_reference'] = self.env['stock.picking'].browse(vals['stock_picking_id'])._get_ship_reference()
        return super(SaleOrderToSend, self).create(vals)

    @api.model
    def write(self, vals):
        if vals.get('delivery_carrier_id'):
            carrier = None
            picking = None
            if vals.get('delivery_carrier_id'):
                carrier = self.env['delivery.carrier'].browse(vals['delivery_carrier_id'])
            else:
                carrier = self.delivery_carrier_id

            if vals.get('stock_picking_id'):
                picking = self.env['stock.picking'].browse(vals['stock_picking_id'])
            else:
                picking = self.stock_picking_id

            if not carrier.verify_carrier(picking.partner_id):
                raise UserError(_('The carrier (%s) is not compatible with partner picking (%s).' % (carrier.name, picking.name)))

            if (carrier.carrier_type == 'mrw' and not carrier.mrw_config_id) or (carrier.carrier_type == 'spring' and not carrier.spring_config_id):
                raise UserError(_('The carrier config (%s) is not be configurated.' % carrier.name))

        # Get new shipping reference
        result = super(SaleOrderToSend, self).write(vals)
        return result
