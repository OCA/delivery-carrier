# -*- coding: utf-8 -*-
# Copyright 2013-2017 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from operator import attrgetter

from odoo import _, api, exceptions, fields, models

from ..postlogistics.web_service import PostlogisticsWebService


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_fixed_date = fields.Date(
        "Fixed delivery date", help="Specific delivery date (ZAW3217)"
    )
    delivery_place = fields.Char(
        "Delivery Place", help="For Deposit item service (ZAW3219)"
    )
    delivery_phone = fields.Char(
        "Phone", help="For notify delivery by telephone (ZAW3213)"
    )
    delivery_mobile = fields.Char(
        "Mobile", help="For notify delivery by telephone (ZAW3213)"
    )

    @api.multi
    def postlogistics_cod_amount(self):
        """ Return the Postlogistic Cash on Delivery amount of a picking

        If the picking delivers the whole sales order, we use the total
        amount of the sales order.

        Otherwise, we don't know the value of each picking so we raise
        an error.  The user has to create packages with the cash on
        delivery price on each package.
        """
        self.ensure_one()
        order = self.sale_id
        if not order:
            return 0.0
        if len(order) > 1:
            raise exceptions.Warning(
                _('The cash on delivery amount must be manually specified '
                  'on the packages when a package contains products '
                  'from different sales orders.')
            )
        order_moves = order.mapped('order_line.procurement_ids.move_ids')
        picking_moves = self.move_lines
        # check if the package delivers the whole sales order
        if order_moves != picking_moves:
            raise exceptions.Warning(
                _('The cash on delivery amount must be manually specified '
                  'on the packages when a sales order is delivered '
                  'in several delivery orders.')
            )
        return order.amount_total

    @api.multi
    def _generate_postlogistics_label(self, webservice_class=None,
                                      package_ids=None):
        """ Generate labels and write tracking numbers received """
        self.ensure_one()
        user = self.env.user
        company = user.company_id
        if webservice_class is None:
            webservice_class = PostlogisticsWebService

        if package_ids is None:
            packages = self._get_packages_from_picking()
            packages = sorted(packages, key=attrgetter('name'))
        else:
            # restrict on the provided packages
            package_obj = self.env['stock.quant.package']
            packages = package_obj.browse(package_ids)

        web_service = webservice_class(company)
        res = web_service.generate_label(self,
                                         packages,
                                         user_lang=user.lang)

        if 'errors' in res:
            raise exceptions.Warning('\n'.join(res['errors']))

        def info_from_label(label):
            tracking_number = label['tracking_number']
            return {'file': label['binary'].decode('base64'),
                    'file_type': label['file_type'],
                    'name': tracking_number + '.' + label['file_type'],
                    }

        labels = []
        # if there are no pack defined, write tracking_number on picking
        # otherwise, write it on parcel_tracking field of each pack
        if not packages:
            label = res['value'][0]
            tracking_number = label['tracking_number']
            self.carrier_tracking_ref = tracking_number
            info = info_from_label(label)
            info['package_id'] = False
            labels.append(info)
            return labels

        tracking_refs = []
        for package in packages:
            label = None
            for search_label in res['value']:
                if package.name in search_label['item_id'].split('+')[-1]:
                    label = search_label
                    tracking_number = label['tracking_number']
                    package.parcel_tracking = tracking_number
                    tracking_refs.append(tracking_number)
                    break
            info = info_from_label(label)
            info['package_id'] = package.id
            labels.append(info)

        self.carrier_tracking_ref = "; ".join(tracking_refs)

        return labels

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """ Add label generation for Postlogistics """
        self.ensure_one()
        if self.carrier_id.delivery_type == 'postlogistics':
            return self._generate_postlogistics_label(package_ids=package_ids)
        _super = super(StockPicking, self)
        return _super.generate_shipping_labels(package_ids=package_ids)


class ShippingLabel(models.Model):
    """ Child class of ir attachment to identify which are labels """
    _inherit = 'shipping.label'

    @api.model
    def _get_file_type_selection(self):
        """ Return a concatenated list of extensions of label file format
        plus file format from super

        This will be filtered and sorted in __get_file_type_selection

        :return: list of tuple (code, name)

        """
        file_types = super(ShippingLabel, self)._get_file_type_selection()
        new_types = [('eps', 'EPS'),
                     ('gif', 'GIF'),
                     ('jpg', 'JPG'),
                     ('png', 'PNG'),
                     ('pdf', 'PDF'),
                     ('spdf', 'sPDF'),  # sPDF is a pdf without integrated font
                     ('zpl2', 'ZPL2')]
        file_types.extend(new_types)
        return file_types
