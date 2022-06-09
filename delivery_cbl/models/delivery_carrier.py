# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("cbl", "CBL")], ondelete={"cbl": "set default"}
    )
    cbl_expenses = fields.Selection(
        string="Type of expenses", selection=[("P", "Prepaid"), ("D", "Due")]
    )

    def _get_cbl_field_error_messages(self):
        return {
            "reference": _("* The reference code field is empty"),
            "c_name": _("* The receiver name field is empty"),
            "c_address": _("* The receiver address field is empty"),
            "c_postal": _("* The receiver postal code field is empty"),
            "c_city": _("* The receiver city field is empty"),
            "packages": _("* The number of package field is empty"),
            "volume": _("* The volume field is empty"),
            "kilos": _("* The kilos field is empty"),
        }

    def _check_cbl_needed_fields(self, vals):
        """
        Check mandatory fields for the file
        """
        self.ensure_one()
        error_fields = self._get_cbl_field_error_messages()
        msg_error = []
        for field, error in error_fields.items():
            if not vals.get(field):
                msg_error.append(error)
        if len(msg_error) > 1:
            raise exceptions.UserError("\n".join(msg_error))

    def _get_cbl_values_for_picking(self, picking):
        self.ensure_one()
        picking.ensure_one()

        def _get_phone(picking):
            phone = picking.partner_id.phone or picking.partner_id.mobile or ""
            phone = phone.replace(" ", "")
            return phone

        number_of_packages = picking.number_of_packages
        consignee = picking.partner_id
        street = consignee.street or ""
        if consignee.street2:
            street += ", {}".format(consignee.street2)
        return {
            "reference": (picking.name or "")[:30],
            "c_name": (consignee.name or "")[:40],
            "c_address": street[:40],
            "c_postal": (consignee.zip or "").replace("-", "")[:7],
            "c_city": (consignee.city or "")[:40],
            "phone": _get_phone(picking)[:15],
            "notes_a": ""[:100],
            "notes_b": ""[:100],
            "packages": str(number_of_packages or 1)[:6],
            "volume": round(picking.volume, 3),
            "kilos": str(round(picking.shipping_weight or 1))[:9],
            "incoterms": self.cbl_expenses,
        }

    def _generate_cbl_txt_format(self, picking):
        values = self._get_cbl_values_for_picking(picking)
        self._check_cbl_needed_fields(values)
        return ";".join(str(value) for value in values.values())

    def generate_cbl_file(self, picking):
        return self._generate_cbl_txt_format(picking)

    def cbl_send_shipping(self, pickings):
        result = []
        for picking in pickings:
            picking.cbl_generate_file()
            tracking_vals = {"tracking_number": "", "exact_price": 0}
            result.append(tracking_vals)
        return result

    def cbl_get_tracking_link(self, picking):
        return ""

    def cbl_rate_shipment(self, order):
        """There's no public API so another price method should be used."""
        return {
            "success": True,
            "price": self.product_id.lst_price,
            "error_message": _(
                "CBL API doesn't provide methods to compute delivery "
                "rates, so you should rely on another price method instead or "
                "override this one in your custom code."
            ),
            "warning_message": _(
                "CBL API doesn't provide methods to compute delivery "
                "rates, so you should rely on another price method instead or "
                "override this one in your custom code."
            ),
        }
