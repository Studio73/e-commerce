# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    # Fix account_journals with missmatch accounts
    cr.execute(
        """
        DELETE FROM bank_payment_line
            WHERE partner_id IS NULL and amount_currency = 0.00;
    """
    )
    cr.execute("SELECT id FROM res_company;")
    companies = cr.fetchall()
    for company in companies:
        cr.execute(
            """
                SELECT id FROM account_account WHERE code ilike '572%%00'
                   AND company_id = %s;
            """,
            (company[0],),
        )
        account_id = cr.fetchone()[0]
        cr.execute(
            """
            UPDATE account_journal SET default_debit_account_id = %s
            WHERE id in (
                SELECT aj.id FROM account_journal aj
                INNER JOIN account_account aa ON aa.id = aj.default_debit_account_id
                WHERE aa.code not ilike '572%%' and aj.company_id = %s);
            UPDATE account_journal SET
                default_credit_account_id = default_debit_account_id;
        """,
            (
                account_id,
                company[0],
            ),
        )
    # Remove partner_id from account_journal to avoid
    # migration script error ambigous column
    # .../openupgrade_scripts/scripts/account/14.0.1.1/pre-migration.py#L439
    cr.execute("ALTER table account_journal DROP COLUMN IF EXISTS partner_id;")
    # FIX multi-company partners
    cr.execute(
        """
        UPDATE res_partner SET company_id = null
        WHERE id IN (
            SELECT DISTINCT a.partner_id FROM account_move_line a
            INNER JOIN res_partner p ON a.partner_id = p.id
            WHERE a.company_id != p.company_id);
    """
    )
    # FIX Delete account_tax_template without related ir_model_data
    cr.execute(
        """
        DELETE FROM account_tax_template WHERE id NOT IN (
            SELECT res_id FROM ir_model_data WHERE model = 'account.tax.template');
    """
    )
