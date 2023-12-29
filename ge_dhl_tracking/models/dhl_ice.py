from odoo import models, fields


class DHLIce(models.Model):
    _name = "dhl.ice"

    code = fields.Char()
    name = fields.Char(translate=True)
