import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_delivery_carrier_label>=16.0dev,<16.1dev',
        'odoo-addon-delivery_auto_refresh>=16.0dev,<16.1dev',
        'odoo-addon-delivery_automatic_package>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_account>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_agency>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_info>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_max_weight_constraint>=16.0dev,<16.1dev',
        'odoo-addon-delivery_cttexpress>=16.0dev,<16.1dev',
        'odoo-addon-delivery_package_number>=16.0dev,<16.1dev',
        'odoo-addon-delivery_package_type_number_parcels>=16.0dev,<16.1dev',
        'odoo-addon-delivery_postlogistics>=16.0dev,<16.1dev',
        'odoo-addon-delivery_postlogistics_server_env>=16.0dev,<16.1dev',
        'odoo-addon-delivery_price_method>=16.0dev,<16.1dev',
        'odoo-addon-delivery_state>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_delivery_link>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
