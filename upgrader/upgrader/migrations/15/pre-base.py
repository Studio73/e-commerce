#!/usr/bin/env python3
# (c) Studio73 - Oscar Segui <oscar@studio73.es>


def migrate(cr):
    cr.execute(
        """
        SELECT count(*) FROM information_schema.tables
        WHERE table_name = 'sale_commission_settlement_line';
    """
    )
    tables = cr.fetchone()
    if tables:
        cr.execute(
            """
            ALTER TABLE sale_commission_settlement_line
            RENAME COLUMN commission_id TO commission_id_old;
        """
        )
