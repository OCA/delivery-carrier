# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from werkzeug.exceptions import Forbidden, NotFound, Unauthorized

from odoo import _, http


class PaazlController(http.Controller):
    @http.route(
        "/_paazl/push_api/v1", auth="none", type="json", csrf=False, methods=["post"]
    )
    def push_api(self):
        """Implement paazl's push api to pick up status changes"""
        env = http.request.env
        bearer_token = http.request.httprequest.headers.get("authorization", "")[
            len("Bearer ") :
        ]
        account = (
            env["carrier.account"]
            .sudo()
            .search(
                [
                    ("delivery_type", "=", "paazl"),
                    ("paazl_bearer_token", "=", bearer_token),
                ],
                limit=1,
            )
        )
        if not account:
            raise (bearer_token and Forbidden or Unauthorized)()
        data = http.request.jsonrequest
        if str(data["webshop"]) != account.account:
            raise Forbidden()
        picking = self._push_api_get_picking(account, data)
        if not picking:
            raise NotFound()
        handler = getattr(
            self,
            "_push_api_handle_%s" % data["status"].lower(),
            self._push_api_post_update,
        )
        return handler(picking, account, data)

    def _push_api_handle_created(self, picking, account, data):
        picking.write({"paazl_carrier_tracking_url": data["trackTraceURL"]})
        return self._push_api_post_update(picking, account, data)

    def _push_api_post_update(self, picking, account, data, attach_data=True):
        """Inform about an update"""
        return picking.message_post(
            _("Update from paazl: %s")
            % (
                # docs say carrierStatus is not used yet, but might eventually
                data.get("carrierStatus", {}).get("description")
                or data["status"]
            ),
            attachments=attach_data and [("paazl.json", json.dumps(data))] or [],
        )

    def _push_api_get_picking(self, account, data):
        """Return the shipping that matches the data we got passed"""
        return (
            http.request.env["stock.picking"]
            .sudo()
            .search(
                [
                    ("name", "=", data["orderReference"]),
                    ("company_id", "=?", account.company_id.id),
                ],
                limit=1,
            )
        )
