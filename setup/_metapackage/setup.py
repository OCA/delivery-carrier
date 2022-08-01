import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-delivery-carrier",
    description="Meta package for oca-delivery-carrier Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-delivery_carrier_info>=15.0dev,<15.1dev',
        'odoo-addon-partner_delivery_zone>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
