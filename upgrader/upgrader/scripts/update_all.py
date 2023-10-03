#!/usr/bin/env click-odoo
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


env = env  # noqa: F821

def clean_views(cr):
    cr.execute(
        """
        DELETE FROM ir_asset;
        DELETE FROM ir_filters;
        DELETE FROM ir_model_data where model = 'ir.filters';
        DELETE FROM ir_rule;
        DELETE FROM ir_model_data where model = 'ir.rule';
        DELETE FROM report_layout;
        DELETE FROM ir_model_data where model = 'report.layout';
        DELETE FROM ir_cron;
        DELETE FROM ir_model_data where model = 'ir.cron';
        DELETE FROM ir_actions where id
            not in (select action_server_id from base_automation);
        DELETE FROM ir_model_data where model = 'ir.actions'
            and res_id not in (select action_server_id from base_automation);
        DELETE FROM ir_act_window;
        DELETE FROM ir_model_data where model = 'ir.actions.act_window';
        DELETE FROM ir_ui_menu;
        DELETE FROM ir_model_data where model = 'ir.ui.menu';
        DELETE FROM ir_ui_view WHERE type != 'qweb';
        DELETE FROM ir_model_data WHERE model = 'ir.ui.view'
            AND res_id IN (SELECT id FROM ir_ui_view WHERE type != 'qweb');
    """
    )
clean_views(env.cr)
env["ir.module.module"].search([("name", "=", "base")]).button_immediate_upgrade()
clean_views(env.cr)
