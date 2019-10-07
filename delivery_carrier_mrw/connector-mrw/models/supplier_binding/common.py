# -*- coding: utf-8 -*-
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action


class SupplierBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Supplier and Odoo
    (``supplier.res.partner``, ``supplier.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'supplier.binding'
    _inherit = 'external.binding'
    _description = 'Supplier Binding (abstract)'

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='supplier.backend',
        string='Supplier Backend',
        required=True,
        ondelete='restrict',
    )
    # fields.Char because 0 is a valid Supplier ID
    external_id = fields.Char(string='ID on supplier')

    _sql_constraints = [
        ('supplier_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same supplier ID.'),
    ]

    @job(default_channel='root.supplier')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on supplier """
        if filters is None:
            filters = {}
        elif filters.get('importer'):
            backend.current_importer = filters['importer']
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.supplier')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a supplier record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=False)
