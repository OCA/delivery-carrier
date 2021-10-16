import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-base_delivery_carrier_label',
        'odoo9-addon-delivery_carrier_deposit',
        'odoo9-addon-delivery_carrier_label_batch',
        'odoo9-addon-delivery_carrier_label_postlogistics',
        'odoo9-addon-delivery_dropoff_site',
        'odoo9-addon-delivery_multi_destination',
        'odoo9-addon-delivery_roulier',
        'odoo9-addon-delivery_roulier_dpd',
        'odoo9-addon-sale_delivery_rate',
        'odoo9-addon-stock_picking_delivery_rate',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 9.0',
    ]
)
