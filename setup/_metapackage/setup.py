import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-delivery_carrier_agency>=16.0dev,<16.1dev',
        'odoo-addon-delivery_carrier_info>=16.0dev,<16.1dev',
        'odoo-addon-delivery_cttexpress>=16.0dev,<16.1dev',
        'odoo-addon-delivery_package_number>=16.0dev,<16.1dev',
        'odoo-addon-delivery_price_method>=16.0dev,<16.1dev',
        'odoo-addon-delivery_state>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
