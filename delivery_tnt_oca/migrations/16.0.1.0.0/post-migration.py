# Copyright 2023 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    old_packaging = env.ref("product_packaging_tnt_default", raise_if_not_found=False)
    if not old_packaging:
        return
    carriers = env["delivery.carrier"].search(
        [
            ("delivery_type", "=", "tnt_oca"),
            ("tnt_default_packaging_id", "=", old_packaging.id),
        ]
    )
    carriers.write({"tnt_default_packaging_id": env.ref("package_type_tnt_default").id})
