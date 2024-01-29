# © 2022 - FactorLibre - Jore Martínez <jorge.martinez@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json

# from odoo.addons.queue_job.job import job
from odoo import http
from odoo.http import request


class DelivereaWebhook(http.Controller):
    @http.route(
        ["/deliverea-tracking-webhook"],
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
        no_jsonrpc=True,
    )
    def order_import_webhook(self, **post):
        SudoStockPicking = request.env["stock.picking"].sudo()
        data = json.loads(
            request.httprequest.data.decode(request.httprequest.charset or "utf-8")
        )
        for line in data:
            SudoStockPicking.deliverea_update_tracking_state(line)
        return self.return_response("Tracking OK")

    @staticmethod
    def return_response(msg, code=200):
        return http.Response(
            json.dumps({"message": msg, "status": code}),
            code,
            headers=[("Content-Type", "application/json")],
        )
