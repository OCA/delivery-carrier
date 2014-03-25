# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
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
from openerp.osv import orm

from postlogistics.web_service import PostlogisticsWebService


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def _generate_postlogistics_label(self, cr, uid, picking,
                                      webservice_class=None, context=None):
        """ Generate labels and write tracking numbers received """
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        company = user.company_id
        if webservice_class is None:
            webservice_class = PostlogisticsWebService

        web_service = webservice_class(company)
        res = web_service.generate_label(picking, user.lang)

        if 'errors' in res:
            raise orm.except_orm('Error', '\n'.join(res['errors']))

        trackings = set([line.tracking_id for line in picking.move_lines])

        labels = []
        # if there are no pack defined, write tracking_number on picking
        # otherwise, write it on serial field of each pack
        for track in trackings:
            if not track:
                # ignore lines without tracking when there is tracking
                # in a picking
                if len(trackings) > 1:
                    continue
                label = res['value'][0]
                tracking_number = label['tracking_number']
                self.write(cr, uid, picking.id,
                           {'carrier_tracking_ref': tracking_number},
                           context=context)
            else:
                label = None
                for search_label in res['value']:
                    if track.name in search_label['item_id'].split('+')[-1]:
                        label = search_label
                        tracking_number = label['tracking_number']
                        track.write({'serial': tracking_number})
                        break
            labels.append({'tracking_id': track and track.id or False,
                           'file': label['binary'].decode('base64'),
                           'file_type': label['file_type'],
                           'name': tracking_number,
                           })

        return labels

    def generate_shipping_labels(self, cr, uid, ids, context=None):
        """ Add label generation for Postlogistics """
        if isinstance(ids, (long, int)):
            ids = [ids]
        assert len(ids) == 1
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking.carrier_id.type == 'postlogistics':
            return self._generate_postlogistics_label(cr, uid, picking,
                                                      context=context)
        return super(stock_picking, self
                     ).generate_shipping_labels(cr, uid, ids, context=context)


class ShippingLabel(orm.Model):
    """ Child class of ir attachment to identify which are labels """
    _inherit = 'shipping.label'

    def _get_file_type_selection(self, cr, uid, context=None):
        """ Return a concatenated list of extensions of label file format
        plus file format from super

        This will be filtered and sorted in __get_file_type_selection

        :return: list of tuple (code, name)

        """
        file_types = super(ShippingLabel, self
                           )._get_file_type_selection(cr, uid, context=context)
        new_types = [('eps', 'EPS'),
                     ('gif', 'GIF'),
                     ('jpg', 'JPG'),
                     ('png', 'PNG'),
                     ('pdf', 'PDF'),
                     ('spdf', 'sPDF'), # sPDF is a pdf without integrated font
                     ('zpl2', 'ZPL2')]
        file_types.extend(new_types)
        return file_types
