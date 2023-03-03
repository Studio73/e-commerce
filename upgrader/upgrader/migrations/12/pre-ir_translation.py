# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>


def migrate(cr):
    """
    FIX QueryCanceled: canceling statement due to statement timeout
    openupgrader 12.0 base/migrations/12.0.1.3/end-migration.py
    As we don't need to preseve the translations its ok delete all to prevent the error
    """
    cr.execute("DELETE FROM ir_translation")
