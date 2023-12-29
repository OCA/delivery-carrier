from odoo import models, fields


class DHLRic(models.Model):
    _name = "dhl.ric"

    code = fields.Char()
    name = fields.Char(translate=True)
