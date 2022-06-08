# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _dpd_fr_soap_get_service(self, account, package=None):
        service = self._roulier_get_service(account, package=package)
        service.update(
            {
                "customerCountry": account.dpd_fr_soap_customer_country,
                "customerId": account.dpd_fr_soap_customer_id,
                "agencyId": account.dpd_fr_soap_agency_id,
                "reference1": self.sale_id.name or self.origin,
            }
        )
        if self.carrier_code == "DPD_Relais":
            service["dropOffLocation"] = self._dpd_dropoff_site()
            service["notifications"] = "AutomaticSMS"
        if self.carrier_code == "DPD_Predict":
            service["notifications"] = "Predict"
        return service

    def _dpd_dropoff_site(self):
        self.ensure_one()
        return ""  # like P22895 TODO implement this
