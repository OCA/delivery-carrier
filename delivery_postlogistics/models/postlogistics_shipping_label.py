# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PostlogisticsShippingLabel(models.Model):
    """ Child class of ir attachment to identify which are labels """

    _name = "postlogistics.shipping.label"
    _inherits = {"ir.attachment": "attachment_id"}
    _description = "Shipping Label for Postlogistics"

    file_type = fields.Char(string="File type", default="pdf")
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachement",
        required=True,
        ondelete="cascade",
    )

    # TODO: check if we can remove this method
    @api.model
    def _selection_file_type(self):
        """ Return a concatenated list of extensions of label file format
        plus file format from super

        This will be filtered and sorted in __get_file_type_selection

        :return: list of tuple (code, name)

        """
        file_types = super()._selection_file_type()
        new_types = [
            ("eps", "EPS"),
            ("gif", "GIF"),
            ("jpg", "JPG"),
            ("png", "PNG"),
            ("pdf", "PDF"),
            ("spdf", "sPDF"),  # sPDF is a pdf without integrated font
            ("zpl2", "ZPL2"),
        ]
        file_types.extend(new_types)
        return file_types
