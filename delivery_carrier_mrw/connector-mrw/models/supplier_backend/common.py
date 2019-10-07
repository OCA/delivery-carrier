# -*- coding: utf-8 -*-
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta

from decorator import contextmanager
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.connector.checkpoint import checkpoint

from ...components.backend_adapter import SupplierAPI

_logger = logging.getLogger(__name__)

IMPORT_DELTA_BUFFER = 120  # seconds


class SupplierBackend(models.Model):
    _name = 'supplier.backend'
    _description = 'Supplier Backend'
    _inherit = 'connector.backend'

    name = fields.Char('name', required=True, readonly=True, related='supplier_id.name')
    no_product_sync = fields.Boolean(string='No sync import products')
    compute_stock = fields.Boolean(string='Compute stock from supplier')
    web = fields.Char('Website', readonly=True, related='supplier_id.website')
    country_id = fields.Many2one('Website', readonly=True, related='supplier_id.country_id')

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse used to compute the '
             'stock quantities.',
    )

    supplier_id = fields.Many2one('res.partner',
                                  'Supplier of products for import',
                                  domain=[('supplier', '=', True)],
                                  ondelete='cascade',
                                  required=True)

    product_binding_ids = fields.One2many(
        comodel_name='supplier.product.product',
        inverse_name='backend_id',
        string='Supplier Products',
        readonly=True,
    )

    product_prefix = fields.Char(
        string='Product Prefix',
        help="A prefix put before the name of imported sku products.",

    )

    team_id = fields.Many2one(comodel_name='crm.team', string='Purchase Team')

    importer_ids = fields.One2many('importer.supplier', 'backend_id', 'Importer product\'s supplier')

    discount = fields.Float('Discount on prices of the backend (in percentage)')

    delay = fields.Integer('Time to wait from purchase is done to the products are received', default=2)

    _sql_constraints = [
        ('product_prefix_uniq', 'unique(product_prefix)',
         "A backend with the same product prefix already exists")
    ]

    @api.multi
    def add_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        return checkpoint.add_checkpoint(self.env, record._name, record.id,
                                         self._name, self.id)

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        # We create a Supplier Client API here, so we can create the
        # client once (lazily on the first use) and propagate it
        # through all the sync session, instead of recreating a client
        # in each backend adapter usage.
        with SupplierAPI(self) as supplier_api:
            _super = super(SupplierBackend, self)
            # from the components we'll be able to do: self.work.supplier_api
            with _super.work_on(
                    model_name, supplier_api=supplier_api, **kwargs) as work:
                yield work

    @api.multi
    def _import_product_product(self):
        for backend in self:
            if not backend.no_product_sync:
                user = backend.warehouse_id.company_id.user_tech_id
                if not user:
                    user = self.env['res.users'].browse(self.env.uid)

                supplier_product = self.env['supplier.product.product']
                if user != self.env.user:
                    supplier_product = supplier_product.sudo(user)

                for importer in backend.importer_ids:
                    try:
                        filters = {'importer':importer}
                        backend.current_importer = importer
                        delayable = supplier_product.with_delay(priority=1, eta=datetime.now())
                        delayable.import_batch(backend, filters=filters)
                    except:
                        _logger.error("Creating import_batch with the %s backend", backend.name)

        # On Supplier we haven't a modified date on products and we need to import all inventory
        return True

    @api.multi
    def _fix_inconsistent_data(self):
        if self:
            backend = self[0]
            backend.current_importer = None
            with backend.work_on(self._name) as work:
                fix_data = work.component(usage='supplier.fix.data')
                fix_data.run()

        return True

    @api.model
    def _supplier_backend(self, callback, domain=None):
        if domain is None:
            domain = []
        backends = self.search(domain)
        if backends:
            getattr(backends, callback)()

    @api.model
    def _scheduler_import_product_product(self, domain=None):
        self._supplier_backend('_import_product_product', domain=domain)

    @api.model
    def _scheduler_connector_supplier_fix_data(self, domain=None):
        self._supplier_backend('_fix_inconsistent_data', domain=domain)

    def execute_backend(self):
        self._import_product_product()


class ImporterSupplier(models.Model):
    _name = 'importer.supplier'

    backend_id = fields.Many2one('supplier.backend', 'Backend of importer', ondelete='cascade')

    tax_included = fields.Boolean('Tax included in price')
    override_images = fields.Boolean('Override images when update products')
    active = fields.Boolean(default=True)

    importer_type = fields.Selection(
        [('web', 'Web crawler'), ('CSV', 'Csv with url user and password')],
        string='Type import data',
        default='web',
        store=True,
        required=True)

    importer_web_id = fields.Many2one('importer.supplier.webcrawler',
                                      string='Web Crawler importer',
                                      ondelete='cascade')

    importer_csv_id = fields.Many2one('importer.supplier.csv',
                                      string='CSV importer',
                                      ondelete='cascade')

    def update_urls(self):
        if self.importer_web_id:
            self.importer_web_id.update_url_child()
