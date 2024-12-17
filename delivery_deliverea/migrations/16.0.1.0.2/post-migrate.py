def migrate(cr, version):
    cr.execute(
        """
        SELECT service_id, parameter_id
        FROM carrier_deliverea_service_carrier_deliverea_parameter_rel
    """
    )
    m2m_data = cr.fetchall()

    # Insertar los datos en la nueva estructura One2many
    for service_id, parameter_id in m2m_data:
        cr.execute(
            """
            UPDATE carrier_deliverea_parameter
            SET service_id = %s
            WHERE id = %s
        """,
            (service_id, parameter_id),
        )
