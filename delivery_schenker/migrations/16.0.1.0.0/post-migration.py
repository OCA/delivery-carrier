# Copyright 2023 Studio73 - Ferran Mora
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    for i in range(1, 23):
        xml_id = "delivery_schenker.schenker_packaging_{}".format(str(i).zfill(2))
        pack = env.ref(xml_id, raise_if_not_found=False)
        if pack:
            xml_id = "delivery_schenker.schenker_package_type_{}".format(
                str(i).zfill(2)
            )
            package_type = env.ref(xml_id, raise_if_not_found=False)
            if package_type:
                env.cr.execute(
                    "SELECT schenker_stackable FROM product_packaging WHERE id=%s",
                    (pack.id,),
                )
                schenker_stackable = env.cr.fetchone()
                package_type.write({"schenker_stackable": schenker_stackable})
