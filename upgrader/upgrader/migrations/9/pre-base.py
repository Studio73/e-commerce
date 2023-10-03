#!/usr/bin/env python3
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    cr.execute(
        """
        DELETE FROM ir_model_constraint WHERE module = (
            SELECT id FROM ir_module_module WHERE name = 'account_analytic_distribution');
        DELETE FROM ir_module_module WHERE name = 'account_analytic_distribution';
        DELETE FROM ir_model_data WHERE name ilike
            '%account_analytic_distribution' and module = 'base';
        ALTER TABLE purchase_order_line ALTER COLUMN state drop not null;
        -- Module uninstallable and wrong dependency
        UPDATE ir_module_module SET state = 'uninstalled'
            WHERE name = 'account_move_line_report_xls';
    """
    )
