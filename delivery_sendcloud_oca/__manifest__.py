# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

{
    "name": "Sendcloud Shipping",
    "summary": "Compute shipping costs and ship with Sendcloud",
    "category": "Operations/Inventory/Delivery",
    "version": "17.0.1.0.0",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Onestein,Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "depends": ["base_address_extended", "stock_delivery", "web", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "security/sendcloud_security_rule.xml",
        "data/delivery_sendcloud_data.xml",
        "data/delivery_sendcloud_cron.xml",
        "data/onboarding_data.xml",
        "wizards/sendcloud_create_return_parcel_wizard_view.xml",
        "views/sale_order_view.xml",
        "views/stock_picking_view.xml",
        "views/stock_warehouse_view.xml",
        "views/res_partner_view.xml",
        "views/delivery_carrier_view.xml",
        "views/sendcloud_parcel_view.xml",
        "views/sendcloud_brand_view.xml",
        "views/sendcloud_carrier_view.xml",
        "views/sendcloud_return_view.xml",
        "views/sendcloud_invoice_view.xml",
        "views/sendcloud_parcel_status_view.xml",
        "views/sendcloud_sender_address_view.xml",
        "views/sendcloud_action.xml",
        "views/sendcloud_integration_view.xml",
        "views/res_config_settings_view.xml",
        "wizards/sendcloud_warehouse_address_wizard_view.xml",
        "wizards/sendcloud_cancel_shipment_confirm_wizard_view.xml",
        "wizards/sendcloud_integration_wizard_view.xml",
        "wizards/sendcloud_sync_wizard_view.xml",
        "wizards/sendcloud_sync_order_wizard_view.xml",
        "wizards/sendcloud_custom_price_details_wizard.xml",
        "views/sendcloud_onboarding_views.xml",
        "views/sendcloud_shipping_method_country_view.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "delivery_sendcloud_oca/static/src/js/*",
            "delivery_sendcloud_oca/static/src/scss/*",
            "delivery_sendcloud_oca/static/src/xml/*",
        ]
    },
    "external_dependencies": {
        "python": [
            # tests dependencies
            "vcrpy",
        ],
    },
    "application": True,
}
