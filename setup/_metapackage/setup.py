import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_delivery_carrier_label>=16.0dev,<16.1dev',
        'odoo-addon-carrier_account_environment>=16.0dev,<16.1dev',
        'odoo-addon-delivery_auto_refresh>=16.0dev,<16.1dev',
        'odoo-addon-delivery_automatic_package>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_account>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_agency>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_deposit>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_info>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_max_weight_constraint>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_partner>=16.0dev,<16.1dev',
        'odoo-addon-delivery_cttexpress>=16.0dev,<16.1dev',
        'odoo-addon-delivery_deliverea>=16.0dev,<16.1dev',
        'odoo-addon-delivery_driver>=16.0dev,<16.1dev',
        'odoo-addon-delivery_driver_stock_picking_batch>=16.0dev,<16.1dev',
        'odoo-addon-delivery_estimated_package_quantity_by_weight>=16.0dev,<16.1dev',
        'odoo-addon-delivery_package_fee>=16.0dev,<16.1dev',
        'odoo-addon-delivery_package_number>=16.0dev,<16.1dev',
        'odoo-addon-delivery_package_type_number_parcels>=16.0dev,<16.1dev',
        'odoo-addon-delivery_postlogistics>=16.0dev,<16.1dev',
        'odoo-addon-delivery_postlogistics_server_env>=16.0dev,<16.1dev',
        'odoo-addon-delivery_price_method>=16.0dev,<16.1dev',
        'odoo-addon-delivery_roulier>=16.0dev,<16.1dev',
        'odoo-addon-delivery_state>=16.0dev,<16.1dev',
        'odoo-addon-partner_delivery_schedule>=16.0dev,<16.1dev',
        'odoo-addon-partner_delivery_zone>=16.0dev,<16.1dev',
        'odoo-addon-server_environment_delivery>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_delivery_link>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_report_delivery_cost>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
