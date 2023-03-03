# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


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


def migrate(cr):
    account_tax(cr)
