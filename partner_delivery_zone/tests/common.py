# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class DeliveryZoneCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_zones()
        cls._setup_zone_partners()

    @classmethod
    def _setup_zones(cls):
        """Two standard zones (A and B) plus an empty one."""
        Zone = cls.env["partner.delivery.zone"]
        cls.delivery_zone_a = Zone.create({"name": "Delivery Zone A", "code": "A"})
        cls.delivery_zone_b = Zone.create({"name": "Delivery Zone B", "code": "B"})

    @classmethod
    def _setup_zone_partners(cls):
        """One partner per zone plus one partner without a zone."""
        Partner = cls.env["res.partner"]
        cls.partner_a = Partner.create(
            {"name": "Customer Zone A", "delivery_zone_id": cls.delivery_zone_a.id}
        )
        cls.partner_b = Partner.create(
            {"name": "Customer Zone B", "delivery_zone_id": cls.delivery_zone_b.id}
        )
        cls.partner_no_zone = Partner.create({"name": "Customer no zone"})
