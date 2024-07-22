import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class EasypostOcaWebhook(models.Model):
    _name = "easypost.oca.webhook"
    _description = "EasypostOcaWebhook"

    name = fields.Char("Name")
    url = fields.Char()
    active = fields.Boolean()
    enviroment = fields.Selection(
        selection=[("production", "Production"), ("test", "Test")]
    )
