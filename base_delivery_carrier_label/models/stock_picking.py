# Copyright 2012-2015 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
        states={'done': [('readonly', True)]},
    )
    delivery_type = fields.Selection(
        related='carrier_id.delivery_type',
        string='Delivery Type',
        readonly=True,
    )
    carrier_code = fields.Char(
        related='carrier_id.code',
        readonly=True,
    )
    option_ids = fields.Many2many(comodel_name='delivery.carrier.option',
                                  string='Options')

    def generate_default_label(self):
        """ Abstract method

        :return: (file_binary, file_type)

        """
        raise NotImplementedError(_('No label is configured for the '
                                    'selected delivery method.'))

    def generate_shipping_labels(self):
        """Generate a shipping label by default

        This method can be inherited to create specific shipping labels
        a list of label must be return as we can have multiple
        stock.quant.package for a single picking representing packs

        :return: list of dict containing
           name: name to give to the attachement
           file: file as string
           file_type: string of file type like 'PDF'
           (optional)
           tracking_number: tracking id defined by your carrier

        """
        self.ensure_one()
        default_label = self.generate_default_label()
        labels = []
        for package in self._get_packages_from_picking():
            pack_label = default_label.copy()
            pack_label['tracking_number'] = package.id
            labels.append(pack_label)
        return labels

    def get_shipping_label_values(self, label):
        self.ensure_one()
        return {
            'name': label['name'],
            'datas_fname': label.get('filename', label['name']),
            'res_id': self.id,
            'res_model': 'stock.picking',
            'datas': base64.b64encode(label['file']),
            'file_type': label['file_type'],
        }

    def generate_labels(self):
        """ Legacy method. Remove me after 12.0
        """
        _logger.warning(
            "Your delivery module depending on your carrier must call "
            "action_generate_carrier_label() method "
            "instead of generate_labels()")
        return self.action_generate_carrier_label()

    def _set_a_default_package(self):
        """ Pickings using this module must have a package
            If not this method put it one silently
        """
        for picking in self:
            move_lines = picking.move_line_ids.filtered(
                lambda s: not (s.package_id or s.result_package_id))
            if move_lines:
                package = self.env['stock.quant.package'].create({})
                move_lines.write({'result_package_id': package.id})

    def action_generate_carrier_label(self):
        """ Method for the 'Generate Label' button.

        It will generate the labels for all the packages of the picking.
        Packages are mandatory in this case

        """
        for pick in self:
            pick._set_a_default_package()
            shipping_labels = pick.generate_shipping_labels()
            for label in shipping_labels:
                data = pick.get_shipping_label_values(label)
                if label.get('package_id'):
                    data['package_id'] = label['package_id']
                context_attachment = self.env.context.copy()
                # remove default_type setted for stock_picking
                # as it would try to define default value of attachement
                if 'default_type' in context_attachment:
                    del context_attachment['default_type']
                self.env['shipping.label'].with_context(
                    context_attachment).create(data)
            if len(shipping_labels) == 1:
                pick.write(
                    {'carrier_tracking_ref': label.get('tracking_number')})
        return True

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        """ Inherit this method in your module """
        if not self.carrier_id:
            return
        # This can look useless as the field carrier_code and
        # carrier_type are related field. But it's needed to fill
        # this field for using this fields in the view. Indeed the
        # module that depend of delivery base can hide some field
        # depending of the type or the code
        carrier = self.carrier_id
        self.update({
            'delivery_type': carrier.delivery_type,
            'carrier_code': carrier.code,
        })
        default_options = carrier.default_options()
        self.option_ids = [(6, 0, default_options.ids)]
        result = {
            'domain': {
                'option_ids': [('id', 'in', carrier.available_option_ids.ids)],
            }
        }
        return result

    @api.onchange('option_ids')
    def onchange_option_ids(self):
        if not self.carrier_id:
            return
        carrier = self.carrier_id
        for available_option in carrier.available_option_ids:
            if (available_option.mandatory and
                    available_option not in self.option_ids):
                # XXX the client does not allow to modify the field that
                # triggered the onchange:
                # https://github.com/odoo/odoo/issues/2693#issuecomment-56825399
                # Ideally we should add the missing option
                raise UserError(
                    _("You should not remove a mandatory option."
                      "Please cancel the edit or "
                      "add back the option: %s.") % available_option.name
                )

    @api.model
    def _values_with_carrier_options(self, values):
        values = values.copy()
        carrier_id = values.get('carrier_id')
        option_ids = values.get('option_ids')
        if carrier_id and not option_ids:
            carrier_obj = self.env['delivery.carrier']
            carrier = carrier_obj.browse(carrier_id)
            default_options = carrier.default_options()
            if default_options:
                values.update(option_ids=[(6, 0, default_options.ids)])
        return values

    @api.multi
    @api.returns('stock.quant.package')
    def _get_packages_from_picking(self):
        """ Get all the packages from the picking """
        self.ensure_one()
        operation_obj = self.env['stock.move.line']
        packages = self.env['stock.quant.package'].browse()
        operations = operation_obj.search(
            ['|',
             ('package_id', '!=', False),
             ('result_package_id', '!=', False),
             ('picking_id', '=', self.id)]
        )
        for operation in operations:
            # Take the destination package. If empty, the package is
            # moved so take the source one.
            packages |= operation.result_package_id or operation.package_id
        return packages

    @api.multi
    def write(self, vals):
        """ Set the default options when the delivery method is changed.

        So we are sure that the options are always in line with the
        current delivery method.

        """
        vals = self._values_with_carrier_options(vals)
        return super(StockPicking, self).write(vals)

    @api.model
    def create(self, vals):
        """ Trigger onchange_carrier_id on create

        To ensure options are setted on the basis of carrier_id copied from
        Sale order or defined by default.

        """
        vals = self._values_with_carrier_options(vals)
        return super(StockPicking, self).create(vals)

    def _get_label_sender_address(self):
        """ On each carrier label module you need to define
            which is the sender of the parcel.
            The most common case is 'picking.company_id.partner_id'
            and then choose the contact which has the type 'delivery'
            which is suitable for each delivery carrier label module.
            But your client might want to customize sender address
            if he has several brands and/or shops in his company.
            In this case he doesn't want his customer to see
            the address of his company in his transport label
            but instead, the address of the partner linked to his shop/brand

            To reach this modularity, call this method to get sender address
            in your delivery_carrier_label_yourcarrier module, then every
            developer can manage specific needs by inherit this method in
            module like :
            delivery_carrier_label_yourcarrier_yourproject.
        """
        self.ensure_one()
        partner = self.company_id.partner_id
        address_id = partner.address_get(adr_pref=['delivery'])['delivery']
        return self.env['res.partner'].browse(address_id)

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
