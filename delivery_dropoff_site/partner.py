# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 2014 Akretion
#    @author Aymeric Lecomte <aymeric.lecomte@akretion.com>
#            David BEAL <david.beal@akretion.com>
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
###############################################################################

from openerp.osv import orm, fields


def search_domain_key(domain, key):
    "Search 'key' in the first element of each tuple of the 'domain' list"
    for condition in domain:
        if condition[0] == key:
            return True
    return False


class ResPartner(orm.Model):
    _inherit = "res.partner"

    def _get_dropoff_site(self, cr, uid, ids, field_n, arg, context=None):
        res = {}
        for elm in self.browse(cr, uid, ids):
            dropoff = self.pool['partner.dropoff.site'].search(
                cr, uid, [('partner_id', '=', elm.id)], context=context)
            res[elm.id] = False
            if dropoff:
                res[elm.id] = dropoff[0]
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if 'partner_id' in vals:
            self._store_set_values(
                cr, uid, ids, ['dropoff_site_id'], context=context)
        super(ResPartner, self).write(cr, uid, ids, vals, context=context)

    def _dropoffsite_in_partner(self, cr, uid, ids, context=None):
        return ids

    _columns = {
        'dropoff_site_id': fields.function(
            _get_dropoff_site,
            string='Dropoff Site',
            type='many2one',
            relation='partner.dropoff.site',
            store={
                'partner.dropoff.site': (_dropoffsite_in_partner,
                                         ['partner_id'], 10),
            },
            help="... are specific areas where carriers ship merchandises.\n"
                 "Recipients comes pick up their parcels in these sites",),
    }

    def name_search(self, cr, uid, name='', args=None, operator='ilike',
                    context=None, limit=80):
        domain = args
        if domain is None:
            domain = []
        if not search_domain_key(domain, 'dropoff_site_id'):
            domain.append(['dropoff_site_id', '=', False])
        return super(ResPartner, self).name_search(
            cr, uid, name=name, args=domain, operator=operator,
            context=context, limit=limit)

    _sql_constraints = [
        ('dropoff_site_id_uniq', 'unique(dropoff_site_id)',
         "Dropoff Site with the same id already exists : must be unique"),
    ]


class AbstractDropoffSite(orm.AbstractModel):
    """ For performance needs, you may insert raw dropoff datas in an sql
        temporary table. In this cases inherit of this class
    """
    _name = 'abstract.dropoff.site'
    _description = 'Common fields for dropoff tables'

    _columns = {
        'code': fields.char(
            'Dropoff site code',
            size=30,
            help='Code of the site in carrier information system'),
        'weight': fields.float(
            'Weight',
            help='Max weight (kg) for the site per package unit '
            '(from the viewpoint of handling)'),
        'subtype': fields.char(
            'Sub type',
            size=30,
            select=True,
            help="Name/code to define the area : " \
                 "shop, postal center, etc."),
        'latitude': fields.float(
            'lattitude'),
        'longitude': fields.float(
            'longitude'),
    }


class PartnerDropoffSite(orm.Model):
    _name = "partner.dropoff.site"
    _description = "Partner dropoff site (delivery point)"
    _inherit = 'abstract.dropoff.site'
    _inherits = {'res.partner': 'partner_id'}
    _rec_name = 'code'
    _dropoff_type = None

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for site in self.browse(cr, uid, ids, context=context):
            address_name = site.partner_id.name_get(context=context)[0][1]
            res.append((site.id, "%s - %s" % (site.code, address_name)))
        return res

    _columns = {
        'dropoff_type': fields.char(
            'Dropoff type',
            required=True,
            help='example : UPS, Postal area, Fedex, etc.'),
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            required=True,
            ondelete="cascade"),
    }

    def create(self, cr, uid, vals, context=None):
        values = {
            'customer': False,
            'supplier': False,
        }
        vals.update(values)
        return super(PartnerDropoffSite, self).create(
            cr, uid, vals, context=context)
