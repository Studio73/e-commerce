# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def account_analytic(cr):
    # Delete distributions without a analytic account, it means it isn't been used
    cr.execute(
        "SELECT state from ir_module_module where name = 'account_analytic_distribution';"
    )
    state = cr.fetchone()
    if state and state[0] in ["installed", "to upgrade"]:
        cr.execute(
            "DELETE from account_analytic_distribution_rule "
            "where analytic_account_id is null;"
        )


def account_tax(cr):
    # Delete tax templates created by l10n_es_extra_data module
    cr.execute(
        """
        DELETE FROM account_fiscal_position_tax_template WHERE tax_src_id in (
            SELECT res_id from ir_model_data
            WHERE model = 'account.tax.template' and module = 'l10n_es_extra_data'
        );
        DELETE FROM account_tax_template WHERE id IN (
            SELECT res_id FROM ir_model_data WHERE model = 'account.tax.template'
            AND module = 'l10n_es_extra_data'
        );
        DELETE FROM ir_model_data WHERE model = 'account.tax.template'
            AND module = 'l10n_es_extra_data';
    """
    )


def account_asset(cr):
    # Fix account.asset.category with wrong method_percentage
    cr.execute(
        """
        UPDATE account_asset_category
            SET method_percentage = ROUND(method_percentage / 12, 2)
        WHERE method_time='percentage' AND method_period=1 AND method_percentage > 1;
    """
    )


def migrate(cr):
    account_analytic(cr)
    account_tax(cr)
    account_asset(cr)
