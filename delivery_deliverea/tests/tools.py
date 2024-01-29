# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json

import werkzeug

import odoo


class DotDict(dict):
    """Helper for dot.notation access to dictionary attributes
    E.g.
      foo = DotDict({'bar': False})
      return foo.bar
    """

    def __getattr__(self, attrib):
        val = self.get(attrib)
        return DotDict(val) if type(val) is dict else val

    # pylint: disable=missing-return
    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    # pylint: disable=missing-return
    def __setitem__(self, key, value):
        super(DotDict, self).__setitem__(key, value)
        self.__dict__.update({key: value})


class MockObject(object):
    _log_call = []

    def __init__(self, *args, **kwargs):
        self.__dict__ = kwargs


class MockRequest(object):
    """Class with context manager mocking odoo.http.request for tests"""

    def __init__(self, env, **kw):
        app = MockObject(
            routing={
                "type": "http",
                "website": True,
                "multilang": kw.get("multilang", True),
            }
        )
        app.get_db_router = app.bind = app.match = app

        lang = kw.get("lang")
        if not lang:
            lang_code = kw.get("context", {}).get(
                "lang", env.context.get("lang", "en_US")
            )
            lang = env["res.lang"]._lang_get(lang_code)

        context = kw.get("context", {})
        context.setdefault("lang", lang_code)

        httprequest_data = b""
        if kw.get("data", {}):
            httprequest_data = json.dumps(kw.get("data", {})).encode()
        self.request = DotDict(
            {
                "context": context,
                "db": None,
                "env": env,
                "jsonrequest": kw.get("data", {}),
                "httprequest": DotDict(
                    {
                        "path": kw.get("path", "/hello/"),
                        "app": app,
                        "environ": {
                            "REMOTE_ADDR": "127.0.0.1",
                        },
                        "cookies": kw.get("cookies", {}),
                        "user_agent": DotDict({"browser": ""}),
                        "headers": kw.get("headers", {}),
                        "data": httprequest_data,
                        "charset": "utf-8",
                    }
                ),
                "lang": lang,
                "redirect": werkzeug.utils.redirect,
                "session": {
                    "geoip": {
                        "country_code": kw.get("country_code"),
                    },
                    "debug": False,
                    "sale_order_id": kw.get("sale_order_id"),
                },
                "website": kw.get("website"),
                # partial(HttpRequest.render, HttpRequest),
                "render": lambda *args, **kwargs: b"",
            }
        )

    def __enter__(self):
        odoo.http._request_stack.push(self.request)
        return self.request

    def __exit__(self, exc_type, exc_value, traceback):
        odoo.http._request_stack.pop()
