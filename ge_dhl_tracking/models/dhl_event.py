from odoo import models, fields


class DHLEvent(models.Model):
    _name = "dhl.event"

    code = fields.Char()
    name = fields.Char(translate=True)
