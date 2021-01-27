import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-base_delivery_carrier_label',
        'odoo13-addon-delivery_carrier_info',
        'odoo13-addon-delivery_carrier_partner',
        'odoo13-addon-delivery_free_fee_removal',
        'odoo13-addon-delivery_multi_destination',
        'odoo13-addon-delivery_state',
        'odoo13-addon-partner_delivery_schedule',
        'odoo13-addon-partner_delivery_zone',
        'odoo13-addon-stock_picking_report_delivery_cost',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
