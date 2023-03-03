# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    query = """
    DELETE FROM account_tax_template WHERE id IN (
        SELECT res_id FROM ir_model_data
        WHERE module = 'l10n_es_custom_tax'
        AND model = 'account.tax.template'
    );

    DELETE FROM ir_model_data WHERE module = 'l10n_es_custom_tax'
        AND model = 'account.tax.template';

    UPDATE ir_model_data set noupdate='t'
        WHERE model = 'account.tax.template' AND module = 'l10n_es';
    """
    cr.execute(query)
