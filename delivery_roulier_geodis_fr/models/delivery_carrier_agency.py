# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DeliveryCarrierAgency(models.Model):
    _inherit = "delivery.carrier.agency"

    geodis_fr_interchange_sender = fields.Char()
    geodis_fr_interchange_recipient = fields.Char()
    geodis_fr_hub_id = fields.Char()
