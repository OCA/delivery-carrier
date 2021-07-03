# @author Raphael Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from functools import wraps


def implemented_by_carrier(func):
    """Decorator: call _carrier_prefixed method instead.

    Usage:
        @implemented_by_carrier
        def _do_something()
        def _laposte_do_something()
        def _gls_do_something()

    At runtime, picking._do_something() will try to call
    the carrier spectific method or fallback to generic _do_something

    """

    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        fun_name = func.__name__

        def get_delivery_type(cls, *args, **kwargs):
            if hasattr(cls, "delivery_type"):
                return cls.delivery_type
            pickings = [
                obj for obj in args if getattr(obj, "_name", "") == "stock.picking"
            ]
            if len(pickings) > 0:
                return pickings[0].delivery_type
            if cls[0].carrier_id:
                return cls[0].carrier_id.delivery_type

        delivery_type = get_delivery_type(cls, *args, **kwargs)
        fun = "_{}{}".format(delivery_type, fun_name)
        if not hasattr(cls, fun):
            fun = "_roulier%s" % (fun_name)
        return getattr(cls, fun)(*args, **kwargs)

    return wrapper
