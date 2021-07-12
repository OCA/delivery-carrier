import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-base_delivery_carrier_label',
        'odoo14-addon-delivery_carrier_city',
        'odoo14-addon-delivery_carrier_info',
        'odoo14-addon-delivery_multi_destination',
        'odoo14-addon-delivery_package_fee',
        'odoo14-addon-delivery_roulier',
        'odoo14-addon-delivery_roulier_option',
        'odoo14-addon-delivery_state',
        'odoo14-addon-stock_picking_delivery_link',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
