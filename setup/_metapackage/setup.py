import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-base_delivery_carrier_files',
        'odoo8-addon-base_delivery_carrier_files_document',
        'odoo8-addon-base_delivery_carrier_label',
        'odoo8-addon-delivery_carrier_b2c',
        'odoo8-addon-delivery_carrier_deposit',
        'odoo8-addon-delivery_carrier_label_gls',
        'odoo8-addon-delivery_carrier_label_postlogistics',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 8.0',
    ]
)
