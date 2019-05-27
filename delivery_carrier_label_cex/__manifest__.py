{
    'name': 'Correos Express',
    'version': '12.0.1.0.0',
    'category': 'Delivery',
    'license': 'AGPL-3',
    'summary': 'Adds Correos Express Webservices',
    'author': 'PESOL, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/delivery-carrier',
    'depends': [
        'base_delivery_carrier_label',
    ],
    'data': [
        'views/res_company_view.xml'
    ],
    'application': False,
    'installable': True,
}
