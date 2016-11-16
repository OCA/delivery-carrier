# coding: utf-8
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, api, fields, _
from openerp.exceptions import Warning as UserError

logger = logging.getLogger(__name__)


URL_TRACKING = "https://gls-group.eu/FR/fr/suivi-colis?match=%s"


class ShippingLabel(models.Model):
    _inherit = 'shipping.label'

    @api.model
    def _get_file_type_selection(self):
        selection = super(ShippingLabel, self)._get_file_type_selection()
        selection.append(('zpl2', 'ZPL2'))
        selection.append(('text/plain', 'Text'))
        selection = list(set(selection))
        return selection


class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    @api.multi
    def open_tracking_url(self):
        self.ensure_one()
        if self.result_package_id and self.result_package_id.parcel_tracking:
            return self.result_package_id.open_tracking_url()


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    carrier_id = fields.Many2one('delivery.carrier')

    @api.multi
    def _get_carrier_tracking_url(self):
        if self.carrier_id.type == 'gls':
            res = URL_TRACKING % self.parcel_tracking
        return res

    @api.multi
    def open_tracking_url(self):
        self.ensure_one()
        if not self.parcel_tracking:
            raise UserError(
                _("Cannot open tracking URL for this carrier "
                  "because this package "
                  "doesn't have a tracking number."))
        return {
            'type': 'ir.actions.act_url',
            'url': self._get_carrier_tracking_url(),
            'target': 'new',
        }


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    carrier_id = fields.Many2one('delivery.carrier')

    @api.multi
    def do_detailed_transfer(self):
        for transfert in self:
            for item in transfert.item_ids:
                carrier_type = transfert.picking_id.carrier_type
                if carrier_type and carrier_type == 'gls':
                    if not (item.package_id or item.result_package_id):
                        raise UserError(
                            u"All products to deliver for carrier '%s' \n"
                            u"must be put in a parcel."
                            % transfert.picking_id.carrier_id.name)
        return super(StockTransferDetails, self).do_detailed_transfer()
