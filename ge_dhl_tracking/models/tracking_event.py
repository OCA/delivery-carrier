import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class TrackingEvent(models.Model):
    _name = "tracking.event"

    name = fields.Char(help="the field 'event-status' at the api.")
    piece_code = fields.Char(help="=tracking_id")
    event_timestamp = fields.Datetime()
    ice = fields.Char()
    ice_name = fields.Char(compute="_compute_message")
    ric = fields.Char()
    ric_name = fields.Char(compute="_compute_message")

    event_location = fields.Char()
    event_country = fields.Char()
    standard_event_code = fields.Char()
    standard_event_name = fields.Char(compute="_compute_message")
    ruecksendung = fields.Boolean()
    package_id = fields.Many2one("stock.quant.package")

    image = fields.Binary()
    filename = fields.Char(help="Filename for the signature file")

    @api.depends("ice", "ric")
    def _compute_message(self):
        for record in self:
            record.ric_name = (
                self.env["dhl.ric"].search([("code", "=", record.ric)], limit=1).name
            )
            record.ice_name = (
                self.env["dhl.ice"].search([("code", "=", record.ice)], limit=1).name
            )
            record.standard_event_name = (
                self.env["dhl.ric"]
                .search([("code", "=", record.standard_event_code)], limit=1)
                .name
            )
