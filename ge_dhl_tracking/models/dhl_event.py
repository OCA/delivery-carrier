from odoo import fields, models


class DHLEvent(models.Model):
    _name = "dhl.event"

    code = fields.Char()
    name = fields.Char(translate=True)
