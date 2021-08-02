import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-base_delivery_carrier_label',
        'odoo13-addon-delivery_auto_refresh',
        'odoo13-addon-delivery_carrier_info',
        'odoo13-addon-delivery_carrier_partner',
        'odoo13-addon-delivery_carrier_pricelist',
        'odoo13-addon-delivery_carrier_service_level',
        'odoo13-addon-delivery_free_fee_removal',
        'odoo13-addon-delivery_multi_destination',
        'odoo13-addon-delivery_package_fee',
        'odoo13-addon-delivery_package_number',
        'odoo13-addon-delivery_postlogistics',
        'odoo13-addon-delivery_postlogistics_server_env',
        'odoo13-addon-delivery_price_method',
        'odoo13-addon-delivery_price_rule_volumetric_weight',
        'odoo13-addon-delivery_purchase',
        'odoo13-addon-delivery_send_to_shipper_at_operation',
        'odoo13-addon-delivery_state',
        'odoo13-addon-partner_delivery_schedule',
        'odoo13-addon-partner_delivery_zone',
        'odoo13-addon-server_environment_delivery',
        'odoo13-addon-stock_picking_delivery_link',
        'odoo13-addon-stock_picking_report_delivery_cost',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
