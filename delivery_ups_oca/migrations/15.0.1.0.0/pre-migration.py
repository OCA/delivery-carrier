def migrate(cr, version):
    if not version:
        return

    # Update XML IDs to point to the new model
    cr.execute(
        """
        UPDATE ir_model_data
        SET model = 'stock.package.type'
        WHERE model = 'product.packaging'
        AND module = 'delivery_ups_oca'
        AND name LIKE 'product_packaging_ups_%'
        """
    )

    # Copy data from product.packaging to stock.package.type
    cr.execute(
        """
        INSERT INTO stock_package_type
            (name, package_carrier_type, shipper_package_code,
             create_uid, create_date, write_uid, write_date)
        SELECT
            name, package_carrier_type, shipper_package_code,
            create_uid, create_date, write_uid, write_date
        FROM product_packaging
        WHERE package_carrier_type = 'ups'
        AND shipper_package_code IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )
