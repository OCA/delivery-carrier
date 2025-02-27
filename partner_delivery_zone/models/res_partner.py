# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_zone_id = fields.Many2one(
        comodel_name="partner.delivery.zone",
        string="Delivery Zone",
        ondelete="restrict",
        index=True,
    )

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        """The purpose of this is to write a context on "child_ids" field
        respecting other contexts on this field.
        """
        res = super().get_view(view_id, view_type, **options)
        if view_type == "form":
            partner_xml = etree.XML(res["arch"])
            partner_fields = partner_xml.xpath("//field[@name='child_ids']")
            if partner_fields:
                partner_field = partner_fields[0]
                context = partner_field.attrib.get("context", "{}").replace(
                    "{", "{'default_delivery_zone_id': delivery_zone_id, ", 1
                )
                partner_field.attrib["context"] = context
                res["arch"] = etree.tostring(partner_xml)
        return res
