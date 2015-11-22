# -*- coding: utf-8 -*-
from openerp import models, api, _
from openerp.exceptions import Warning as UserError


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @api.multi
    def get_weight(self):
        """ Compute the weight of a pack

        Get all the children packages and sum the weight of all
        the product and the weight of the Logistic Units of the packages.

        So if I put in PACK65:
         * 1 product A of 2kg
         * 2 products B of 4kg
        The box of PACK65 weights 0.5kg
        And I put in PACK66:
         * 1 product A of 2kg
        The box of PACK66 weights 0.5kg

        Then I put PACK65 and PACK66 in the PACK67 having a box that
        weights 0.5kg, the weight of PACK67 should be: 13.5kg

        """
        self.ensure_one()
        pack_op_obj = self.env['stock.pack.operation']
        weight = 0
        packages = self.search([('id', 'child_of', self.id)])
        for package in packages:
            operations = pack_op_obj.search(
                ['|',
                 '&',
                 ('package_id', '=', package.id),
                 ('result_package_id', '=', False),
                 ('result_package_id', '=', package.id),
                 ('product_id', '!=', False),
                 ])
            for operation in operations:
                weight += operation.product_id.weight * operation.product_qty

            if package.ul_id:
                weight += package.ul_id.weight
        return weight


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def set_pack_weight(self):
        # I cannot loop on the "quant_ids" of packages, because, at this step,
        # this field doesn't have a value yet
        self.ensure_one()
        for packop in self.pack_operation_ids:
            package = packop.result_package_id or packop.package_id
            if package:
                weight = package.get_weight()
                package.write({'weight': weight})
        return

    @api.multi
    def _check_existing_shipping_label(self):
        """ Check that labels don't already exist for this picking """
        self.ensure_one()
        labels = self.env['shipping.label'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', 'stock.picking')])
        if labels:
            raise UserError(
                _('Some labels already exist for the picking %s.\n'
                  'Please delete the existing labels in the '
                  'attachments of this picking and try again')
                % self.name)
