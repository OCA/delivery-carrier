from odoo import fields, models


class DHLIce(models.Model):
    _name = "dhl.ice"

    code = fields.Char()
    name = fields.Char(translate=True)
