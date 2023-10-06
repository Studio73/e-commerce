#!/usr/bin/env python3
# (c) Studio73 - Oscar Segui <oscar@studio73.es>


def migrate(cr):
    cr.execute(
        """
        SELECT count(*) FROM ir_module_module WHERE name = 'edi';
    """
    )
    modules = cr.fetchone()
    if modules:
        cr.execute(
            """
            ALTER TABLE edi_exchange_type ADD COLUMN model_manual_btn BOOLEAN;
        """
        )
