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
from operator import attrgetter

from openerp.osv import orm, fields

from .postlogistics.web_service import PostlogisticsWebService


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def _tracking_url(self, cr, uid, ids, name, args, context=None):
        """ Create an url from tracking refs to link with postlogistic website
        @return: Dictionary of values
        """
        base_url = ("http://www.post.ch/swisspost-tracking?p_language=%(lang)s"
                    "&formattedParcelCodes=%(refs)s")
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):
            refs = pick.carrier_tracking_ref
            if not refs:
                res[pick.id] = False
                continue
            # references are separated by ';' + space
            # we need to remove the space to use them in url
            refs = "".join(refs.split())
            lang = pick.partner_id.lang
            if lang:
                lang = lang[:2]
            if not lang or lang not in ('en', 'de', 'fr', 'it'):
                lang = 'en'
            res[pick.id] = base_url % {'lang': lang, 'refs': refs}
        return res

    _columns = {
        'cash_on_delivery': fields.float(
            "Cash on Delivery", help="Amount for Cash on delivery service (N)"
        ),
        'delivery_fixed_date': fields.date(
            "Fixed delivery date", help="Specific delivery date (ZAW3217)"
        ),
        'delivery_place': fields.char(
            "Delivery Place", help="For Deposit item service (ZAW3219)"
        ),
        'delivery_phone': fields.char(
            "Phone", help="For notify delivery by telephone (ZAW3213)"
        ),
        'delivery_mobile': fields.char(
            "Mobile", help="For notify delivery by telephone (ZAW3213)"
        ),
        # remove size constraint of 32 characters
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=None),
        'carrier_tracking_url': fields.function(
            _tracking_url, type='char', string='Tracking URL',
        ),
    }

    def _generate_postlogistics_label(self, cr, uid, picking,
                                      webservice_class=None,
                                      tracking_ids=None, context=None):
        """ Generate labels and write tracking numbers received """
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        company = user.company_id
        if webservice_class is None:
            webservice_class = PostlogisticsWebService

        if tracking_ids is None:
            # get all the trackings of the picking
            # if there is no tracking, an empty list will be returned
            trackings = set()
            for move_line in picking.move_lines:
                if move_line.tracking_id:
                    trackings.add(move_line.tracking_id)
            trackings = sorted(trackings, key=attrgetter('name'))
        else:
            # restrict on the provided trackings
            tracking_obj = self.pool['stock.tracking']
            trackings = tracking_obj.browse(cr, uid, tracking_ids,
                                            context=context)

        web_service = webservice_class(company)
        res = web_service.generate_label(picking,
                                         trackings,
                                         user_lang=user.lang)

        if 'errors' in res:
            raise orm.except_orm('Error', '\n'.join(res['errors']))

        labels = []
        # if there are no pack defined, write tracking_number on picking
        # otherwise, write it on serial field of each pack
        if not trackings:
            label = res['value'][0]
            tracking_number = label['tracking_number']
            self.write(cr, uid, picking.id,
                       {'carrier_tracking_ref': tracking_number},
                       context=context)
            return [{'tracking_id': False,
                     'file': label['binary'].decode('base64'),
                     'file_type': label['file_type'],
                     'name': tracking_number + '.' + label['file_type'],
                     }]

        tracking_refs = []
        for track in trackings:
            label = None
            for search_label in res['value']:
                if track.name in search_label['item_id'].split('+')[-1]:
                    label = search_label
                    tracking_number = label['tracking_number']
                    track.write({'serial': tracking_number})
                    tracking_refs.append(tracking_number)
                    break
            labels.append({'tracking_id': track.id if track else False,
                           'file': label['binary'].decode('base64'),
                           'file_type': label['file_type'],
                           'name': tracking_number + '.' + label['file_type'],
                           })

        tracking_refs = "; ".join(tracking_refs)
        self.write(cr, uid, picking.id,
                   {'carrier_tracking_ref': tracking_refs},
                   context=context)

        return labels

    def generate_shipping_labels(self, cr, uid, ids, tracking_ids=None,
                                 context=None):
        """ Add label generation for Postlogistics """
        if isinstance(ids, (long, int)):
            ids = [ids]
        assert len(ids) == 1
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking.carrier_id.type == 'postlogistics':
            return self._generate_postlogistics_label(
                cr, uid, picking,
                tracking_ids=tracking_ids,
                context=context)
        return super(stock_picking, self).\
            generate_shipping_labels(cr, uid, ids, tracking_ids=tracking_ids,
                                     context=context)


class stock_picking_out(orm.Model):
    _inherit = 'stock.picking.out'

    def _tracking_url(self, *args, **kwargs):
        return self.pool['stock.picking']._tracking_url(*args, **kwargs)

    _columns = {
        'cash_on_delivery': fields.float(
            "Cash on Delivery", help="Amount for Cash on delivery service (N)"
        ),
        'delivery_fixed_date': fields.date(
            "Fixed delivery date", help="Specific delivery date (ZAW3217)"
        ),
        'delivery_place': fields.char(
            "Delivery Place", help="For Deposit item service (ZAW3219)"
        ),
        'delivery_phone': fields.char(
            "Phone", help="For notify delivery by telephone (ZAW3213)"
        ),
        'delivery_mobile': fields.char(
            "Mobile", help="For notify delivery by telephone (ZAW3213)"
        ),
        # remove size constraint of 32 characters
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=None),
        'carrier_tracking_url': fields.function(
            _tracking_url, type='char', string='Tracking URL',
        ),
    }


class stock_picking_in(orm.Model):
    _inherit = 'stock.picking.in'

    def _tracking_url(self, *args, **kwargs):
        return self.pool['stock.picking']._tracking_url(*args, **kwargs)

    _columns = {
        'cash_on_delivery': fields.float(
            "Cash on Delivery", help="Amount for Cash on delivery service (N)"
        ),
        'delivery_fixed_date': fields.date(
            "Fixed delivery date", help="Specific delivery date (ZAW3217)"
        ),
        'delivery_place': fields.char(
            "Delivery Place", help="For Deposit item service (ZAW3219)"
        ),
        'delivery_phone': fields.char(
            "Phone", help="For notify delivery by telephone (ZAW3213)"
        ),
        'delivery_mobile': fields.char(
            "Mobile", help="For notify delivery by telephone (ZAW3213)"
        ),
        # remove size constraint of 32 characters
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=None),
        'carrier_tracking_url': fields.function(
            _tracking_url, type='char', string='Tracking URL',
        ),
    }


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
                     ('spdf', 'sPDF'),  # sPDF is a pdf without integrated font
                     ('zpl2', 'ZPL2')]
        file_types.extend(new_types)
        return file_types
