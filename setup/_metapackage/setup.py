import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-base_delivery_carrier_label',
        'odoo10-addon-delivery_auto_refresh',
        'odoo10-addon-delivery_carrier_b2c',
        'odoo10-addon-delivery_carrier_deposit',
        'odoo10-addon-delivery_carrier_label_postlogistics',
        'odoo10-addon-delivery_dropoff_site',
        'odoo10-addon-delivery_multi_destination',
        'odoo10-addon-delivery_price_rule_untaxed',
        'odoo10-addon-sale_delivery_rate',
        'odoo10-addon-stock_picking_delivery_rate',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
