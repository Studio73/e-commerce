#!/usr/bin/env python3
# (c) Studio73 - Oscar Segui <oscar@studio73.es>


def migrate(cr):
    cr.execute(
        """
        ALTER TABLE account_move_line DROP COLUMN IF EXISTS account_type;
        DELETE FROM ir_model_data WHERE model = 'ir.model.fields' AND name ilike '%field_stock_inventory%';
        DELETE FROM ir_model_fields WHERE ttype='job_serialized';
        UPDATE ir_translation SET state = 'translated' WHERE state = 'to_translate';
    """
    )
