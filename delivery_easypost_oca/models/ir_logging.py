from odoo import fields, models


class IrLogging(models.Model):
    _inherit = "ir.logging"

    type = fields.Selection(
        selection_add=[("easypost_oca", "Easypost OCA")],
        ondelete={"easypost_oca": lambda recs: recs.write({"type": "server"})},
    )
